import csv
import io
import secrets

from flask import (Flask, flash, jsonify, make_response, redirect,
                   render_template, request)
from flask_login import (LoginManager, current_user, login_required,
                         login_user, logout_user)
from sqlalchemy.orm import joinedload

from models import Album, Artist, User, db
from utils import load_user

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.user_loader(load_user)


@login_manager.unauthorized_handler
def unauthorized():
    return redirect("/login")


@app.route("/login", methods=["POST", "GET"])
def login():
    if current_user.is_authenticated:
        return render_template("login.html")

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()

        if user is not None and user.check_password(password):
            login_user(user)
            return redirect("/")
        else:
            flash("Invalid username or password")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")


# artist page
@app.route("/", methods=["POST", "GET"])
@login_required
def artist_list():
    if request.method == "POST":
        try:
            artist_name = request.form["name"]
            artist_genre = request.form["genre"]
            new_artist = Artist(name=artist_name, genre=artist_genre)

        except Exception as e:
            print(str(e))
            return render_template("nice.html")

        # check if the artist already exists (name)
        artist_exists = Artist.query.filter(
            Artist.name.collate("NOCASE") == artist_name).first()
        if artist_exists:
            flash("Artist already exists")
            return redirect("/")

        else:
            try:
                db.session.add(new_artist)
                db.session.commit()
                return redirect("/")

            except Exception as e:
                print(str(e))
                return render_template("error.html")

    else:
        try:
            artists = Artist.query.order_by(Artist.date_created).all()
            return render_template("index.html", artists=artists)

        except Exception as e:
            print(str(e))
            return render_template("error.html")


# delete artist
@app.route("/delete-artist/<int:artist_id>")
@login_required
def delete_artist(artist_id):
    artist_to_delete = Artist.query.get_or_404(artist_id)

    if current_user.is_admin():
        try:
            # first delete all albums associated with the artist
            Album.query.filter_by(artist_id=artist_id).delete()

            # then delete the artist
            db.session.delete(artist_to_delete)
            db.session.commit()
            return redirect("/")

        except Exception as e:
            print(str(e))
            return render_template("error.html")

    else:
        flash("Only admin can delete records from database")
        return redirect("/")


# update artist
@app.route("/update-artist/<int:artist_id>", methods=["POST", "GET"])
@login_required
def update_artist(artist_id):
    artist_to_update = Artist.query.get_or_404(artist_id)
    if request.method == "POST":
        try:
            artist_to_update.name = request.form["name"]
            artist_to_update.genre = request.form["genre"]
            db.session.commit()
            return redirect("/")

        except Exception as e:
            print(str(e))
            return render_template("nice.html")

    else:
        if current_user.is_admin():
            return render_template("update.html", artist=artist_to_update)
        flash("Only admin can update records in database")
        return redirect("/")


# album page
@app.route("/albums", methods=["POST", "GET"])
@login_required
def album_list():
    artists = Artist.query.all()
    if request.method == "POST":
        try:
            album_name = request.form["title"]
            artist_id = request.form["artist_id"]
            new_album = Album(title=album_name, artist_id=artist_id)

        except Exception as e:
            print(str(e))
            return render_template("nice.html")

        # check if the album already exists (title)
        album_exists = (
            Album.query
            .filter(Album.title.collate("NOCASE") == album_name,
                    Album.artist_id == artist_id)
            .first()
        )

        if album_exists:
            flash("Album already exists")
            return redirect("/albums")

        else:
            try:
                db.session.add(new_album)
                db.session.commit()
                return redirect("/albums")

            except Exception as e:
                print(str(e))
                return render_template("error.html")

    else:
        albums = Album.query.options(joinedload(Album.artist)).all()
        return render_template("albums.html", albums=albums, artists=artists)


# delete album
@app.route("/delete-album/<int:album_id>")
@login_required
def delete_album(album_id):
    album_to_delete = Album.query.get_or_404(album_id)

    if current_user.is_admin():
        try:
            db.session.delete(album_to_delete)
            db.session.commit()
            return redirect("/albums")

        except Exception as e:
            print(str(e))
            return render_template("error.html")

    else:
        flash("Only admin can delete records from database")
        return redirect("/albums")


# REST API Route - artists
@app.route("/api/artists")
def get_artists():
    artists = Artist.query.all()
    return jsonify([artist.serialize for artist in artists])


# REST API Route - albums
@app.route("/api/albums")
def get_albums():
    albums = Album.query.all()
    return jsonify([album.serialize for album in albums])


# Export CSV route
@app.route("/export/csv")
@login_required
def export_csv():
    artists = Artist.query.all()
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header row
    writer.writerow(["Artist Name", "Genre", "DB Album Count"])

    # Write data rows
    for artist in artists:
        writer.writerow([artist.name, artist.genre, len(artist.albums)])

    # Set up response object
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=artists.csv"
    response.headers["Content-type"] = "text/csv"

    return response


if __name__ == "__main__":
    app.run(debug=True)
