from flask import Blueprint, redirect, request, url_for, session, render_template
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from services.models import User
from services.spotify_api import sp_oauth
from services.spotify_api import get_user_info
# Inizializzare Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

auth_bp = Blueprint('auth', __name__)

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

@auth_bp.route('/')
def login():
    """ Reindirizza l'utente alla pagina di autenticazione Spotify """
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@auth_bp.route('/logout')
@login_required
def logout():
    """ Disconnette l'utente e cancella la sessione """
    logout_user()
    session.clear()
    return redirect(url_for('home.homepage'))

@auth_bp.route('/callback')
def callback():
    """ Gestisce il callback dopo il login """
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session['token_info'] = token_info

    # Recuperiamo i dati dell'utente da Spotify
    user_info = get_user_info(token_info)
    user = User.find_by_username(user_info['id'])

    if not user:
        user = User.create(user_info['id'], user_info['email'])

    login_user(user)

    return redirect(url_for('home.homepage'))
