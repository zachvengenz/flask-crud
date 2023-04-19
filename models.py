from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pytz

db = SQLAlchemy()

# format the timezone
date_now = datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(pytz.timezone('Europe/Helsinki'))


class Artist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    genre = db.Column(db.String(200), unique=True, nullable=False)
    date_created = db.Column(db.DateTime, default=date_now)
    albums = db.relationship('Album', backref='artist', lazy=True)

    def __repr__(self):
        return "<Artist %r>" % self.id

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'genre': self.genre,
            'date_created': self.date_created.isoformat(),
            'albums': [album.title for album in self.albums]
        }


class Album(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), unique=True, nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'), nullable=False)
    date_created = db.Column(db.DateTime, default=date_now)

    def __repr__(self):
        return "<Album %r>" % self.id

    @property
    def serialize(self):
        return {
            'id': self.id,
            'title': self.title,
            'artist': self.artist.name,
            'date_created': self.date_created.isoformat()
        }
