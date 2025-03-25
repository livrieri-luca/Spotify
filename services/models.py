import pymysql
from flask_login import UserMixin
import os
from dotenv import load_dotenv

# Carica le variabili d'ambiente dal file .env
load_dotenv()

def get_db_connection():
    """Funzione per ottenere una connessione al database."""
    try:
        return pymysql.connect(
            host=os.getenv('DB_HOST'),       # Carica host da variabile d'ambiente
            user=os.getenv('DB_USER'),       # Carica user da variabile d'ambiente
            password=os.getenv('DB_PASSWORD'),  # Carica password da variabile d'ambiente
            database=os.getenv('DB_NAME')    # Carica database da variabile d'ambiente
        )
    except pymysql.MySQLError as e:
        print(f"Errore di connessione al database: {e}")
        return None

# Crea una classe User per gestire gli utenti
class User(UserMixin):
    def __init__(self, id, username, email):
        self.id = id
        self.username = username
        self.email = email

    @staticmethod
    def get(user_id):
        """Trova un utente per ID."""
        conn = get_db_connection()
        if conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id, username, email FROM users WHERE id = %s", (user_id,))
                result = cursor.fetchone()
                return User(result[0], result[1], result[2]) if result else None
        return None

    @staticmethod
    def find_by_username(username):
        """Trova un utente per nome utente."""
        conn = get_db_connection()
        if conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id, username, email FROM users WHERE username = %s", (username,))
                result = cursor.fetchone()
                return User(result[0], result[1], result[2]) if result else None
        return None

    @staticmethod
    def create(username, email):
        """Crea un nuovo utente."""
        conn = get_db_connection()
        if conn:
            with conn.cursor() as cursor:
                cursor.execute("INSERT INTO users (username, email) VALUES (%s, %s)", (username, email))
                conn.commit()
                return User(cursor.lastrowid, username, email)
        return None

# Playlist Model
class Playlist:
    @staticmethod
    def get_playlists(user_id):
        """Recupera tutte le playlist di un utente."""
        conn = get_db_connection()
        if conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM playlists WHERE user_id = %s", (user_id,))
                return cursor.fetchall()
        return []

    @staticmethod
    def add_playlist(user_id, playlist_name):
        """Aggiungi una nuova playlist."""
        conn = get_db_connection()
        if conn:
            with conn.cursor() as cursor:
                cursor.execute("INSERT INTO playlists (user_id, name) VALUES (%s, %s)", (user_id, playlist_name))
                conn.commit()
