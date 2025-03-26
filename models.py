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
class Elemento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)  # ad esempio "canzone", "video", ecc.
    playlist_id = db.Column(db.Integer, db.ForeignKey('lista_playlist.id'), nullable=False)