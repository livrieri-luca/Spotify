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
    # Quando un utente vuole fare il login tramite Spotify, lo reindirizzi alla pagina di autorizzazione di Spotify
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)
@auth_bp.route('/logout')
def logout():
    # Quando l'utente esegue il logout, cancella tutte le sessioni e reindirizzalo al login locale
    session.clear()  # Questo rimuove la sessione di login locale
    return redirect(url_for('auth.loginlocale'))  # Reindirizza alla pagina di login locale

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        
        # Controlla se l'username è già in uso
        if User.query.filter_by(username=username).first():
            flash('Username già in uso.', 'danger')
        else:
            new_user = User(username=username, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash('Registrazione completata! Ora puoi accedere.', 'success')
            return redirect(url_for('auth.loginlocale'))  # Reindirizza alla pagina di login dopo la registrazione

    return render_template('register.html')

@auth_bp.route('/callback')
def callback():
    # Gestisci il callback da Spotify per ottenere il token
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session['token_info'] = token_info  # Salva il token nella sessione

    # Qui dovresti associare l'utente Spotify al tuo sistema se non è già registrato
    sp = spotipy.Spotify(auth=token_info['access_token'])
    user_info = sp.current_user()  # Ottieni le informazioni dell'utente da Spotify

    # Cerca un utente nel database o crea un nuovo utente
    user = User.query.filter_by(username=user_info['id']).first()
    if not user:
        user = User(username=user_info['id'], password=None)  # Non serve la password per Spotify
        db.session.add(user)
        db.session.commit()

    # Fai il login dell'utente localmente
    login_user(user)

    return redirect(url_for('home.homepage'))  # Reindirizza alla home page dopo il login con Spotify


@auth_bp.route('/', methods=['GET', 'POST'])
def loginlocale():
    # Se l'utente è già loggato tramite Spotify, non deve inserire username e password locali
    token_info = session.get('token_info', None)
    if token_info:
        # Se il token esiste, significa che l'utente è già loggato tramite Spotify
        sp = spotipy.Spotify(auth=token_info['access_token'])
        user_info = sp.current_user()
        
        # Cerca o crea un utente nel tuo database
        user = User.query.filter_by(username=user_info['id']).first()
        if not user:
            user = User(username=user_info['id'], password=None)  # Non serve la password per Spotify
            db.session.add(user)
            db.session.commit()
        
        login_user(user)  # Effettua il login dell'utente
        return redirect(url_for('home.homepage'))  # Reindirizza alla homepage
    
    # Se non è stato effettuato il login tramite Spotify, mostra il form di login locale
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)  # Autenticazione tramite login locale
            return redirect(url_for('home.homepage'))  # Reindirizza alla home page normale

        return render_template('login.html', error="Credenziali non valide.")
    
    return render_template('login.html', error=None)
