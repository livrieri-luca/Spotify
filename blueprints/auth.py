from flask import Blueprint, render_template, redirect, request, url_for, flash, session
from flask_login import login_user, logout_user, login_required
from flask_bcrypt import Bcrypt
from models import db, User
import spotipy
from services.spotify_api import sp_oauth

auth_bp = Blueprint('auth', __name__)
bcrypt = Bcrypt()

@auth_bp.route('/ciao', endpoint='login_spotify')
def login():
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.loginlocale'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        if User.query.filter_by(username=username).first():
            flash('Username già in uso.', 'danger')
        else:
            new_user = User(username=username, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash('Registrazione completata! Ora puoi accedere.', 'success')
            return redirect(url_for('auth.loginlocale'))

    return render_template('register.html')

@auth_bp.route('/callback')
def callback():
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session['token_info'] = token_info

    sp = spotipy.Spotify(auth=token_info['access_token'])
    user_info = sp.current_user()

    user = User.query.filter_by(username=user_info['id']).first()
    if not user:
        user = User(username=user_info['id'], password=None)
        db.session.add(user)
        db.session.commit()

    login_user(user)
    return redirect(url_for('home.homepage'))

@auth_bp.route('/', methods=['GET', 'POST'])
def loginlocale():
    # Non eseguire automaticamente il login se non è presente il token Spotify
    token_info = session.get('token_info', None)
    
    # Solo se l'utente è già autenticato tramite Spotify
    if token_info:
        sp = spotipy.Spotify(auth=token_info['access_token'])
        user_info = sp.current_user()

        user = User.query.filter_by(username=user_info['id']).first()
        if not user:
            user = User(username=user_info['id'], password=None)
            db.session.add(user)
            db.session.commit()

        login_user(user)
        flash("Login avvenuto con successo tramite Spotify!", "success")
        return redirect(url_for('home.homepage'))

    # Se la richiesta è un POST (quindi l'utente ha premuto "Accedi")
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Trova l'utente nel database
        user = User.query.filter_by(username=username).first()

        # Verifica le credenziali
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash("Login avvenuto con successo!", "success")
            return redirect(url_for('home.homepage'))
        
        # Se il login fallisce, flash del messaggio di errore
        flash("Credenziali non valide.", "error")
    
    return render_template('login.html')