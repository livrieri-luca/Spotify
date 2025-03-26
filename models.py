from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)

class ListaPlaylist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    utente = db.Column(db.String(80), nullable=False)
    nome = db.Column(db.String(80), nullable=False)
    elemento = db.Column(db.String(100), nullable=False)
