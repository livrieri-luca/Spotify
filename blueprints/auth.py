from flask import Blueprint, redirect, request, url_for, session
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from services.spotify_oauth import sp_oauth, get_spotify_object

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def login():
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@auth_bp.route('/logout')
def logout():
    session.clear()  # Cancella l'access token salvato in sessione
    return redirect(url_for('auth.login'))

@auth_bp.route('/callback')
def callback():
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session['token_info'] = token_info
    return redirect(url_for('home.homepage'))
