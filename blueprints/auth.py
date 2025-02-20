from flask import Blueprint, redirect, request, url_for, session
from services.spotify_oauth import sp_oauth

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def login():
    """ Reindirizza l'utente alla pagina di autenticazione Spotify """
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@auth_bp.route('/logout')
def logout():
    """ Disconnette l'utente e cancella la sessione """
    session.clear()
    return redirect(url_for('home.homepage'))

@auth_bp.route('/callback')
def callback():
    """ Gestisce il callback dopo il login """
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session['token_info'] = token_info
    return redirect(url_for('home.homepage'))
