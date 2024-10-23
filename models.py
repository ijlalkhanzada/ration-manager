from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()


class Record(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    father_name = db.Column(db.String(100))
    address = db.Column(db.String(200))
    contact_number = db.Column(db.String(15))
    is_active = db.Column(db.Boolean, default=True)


class Recipient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    father_name = db.Column(db.String(100))
    address = db.Column(db.String(200))
    contact_number = db.Column(db.String(15))
    is_active = db.Column(db.Boolean, default=True)

class User(db.Model, UserMixin):  # Import UserMixin here
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
