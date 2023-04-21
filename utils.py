from models import User, db
from werkzeug.security import generate_password_hash


def create_users():
    user = User(username='demo_user', password_hash=generate_password_hash('demopw1'), role="user")
    admin = User(username='demo_admin', password_hash=generate_password_hash('demopw2'), role="admin")
    db.session.add(user)
    db.session.add(admin)
    db.session.commit()
