import re
from flask import Blueprint, render_template, redirect, request, url_for, flash, session
from flask_login import login_user, logout_user, login_required
from flask_bcrypt import Bcrypt
from models import db, User
import spotipy
from services.spotify_api import sp_oauth

auth_bp = Blueprint('auth', __name__)
bcrypt = Bcrypt()

# Funzione che controlla se la password rispetta i criteri di sicurezza
def controllaPassword(password):
    if len(password) < 8:
        flash("La password deve contenere almeno 8 caratteri.", "error")
        return False
    if not re.search(r"[A-Z]", password):
        flash("La password deve contenere almeno una lettera maiuscola.", "error")
        return False
    if not re.search(r"[a-z]", password):
        flash("La password deve contenere almeno una lettera minuscola.", "error")
        return False
    if not re.search(r"[0-9]", password):
        flash("La password deve contenere almeno un numero.", "error")
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        flash("La password deve contenere almeno un carattere speciale.", "error")
        return False
    return True

# Rotta per l'autenticazione tramite Spotify
@auth_bp.route('/ciao', endpoint='login_spotify')
def login():
    # Generiamo l'URL per autorizzare l'accesso tramite Spotify
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

# Rotta per il logout dell'utente
@auth_bp.route('/logout')
def logout():
    # Pulisci la sessione dell'utente e lo redirigi alla pagina di login
    session.clear()
    return redirect(url_for('auth.loginlocale'))

# Rotta per la registrazione di un nuovo utente
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Prima di registrare l'utente, verifichiamo che la password sia sicura
        if not controllaPassword(password):
            return render_template('register.html')
        
        # Criptiamo la password prima di salvarla nel database
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Verifichiamo se l'username è già in uso
        if User.query.filter_by(username=username).first():
            flash('Username già in uso.', 'danger')
        else:
            # Creiamo un nuovo utente e lo salviamo nel database
            new_user = User(username=username, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash('Registrazione completata! Ora puoi accedere.', 'success')
            return redirect(url_for('auth.loginlocale'))

    # Se è una richiesta GET, mostriamo la pagina di registrazione
    return render_template('register.html')

# Rotta per il callback dopo che l'utente ha autorizzato l'accesso a Spotify
@auth_bp.route('/callback')
def callback():
    # Recuperiamo il codice di autorizzazione da Spotify
    code = request.args.get('code')
    
    # Otteniamo il token di accesso tramite il codice ricevuto
    token_info = sp_oauth.get_access_token(code)
    session['token_info'] = token_info

    # Creiamo un oggetto Spotify utilizzando il token di accesso
    sp = spotipy.Spotify(auth=token_info['access_token'])
    user_info = sp.current_user()

    # Cerchiamo un utente nel nostro database con l'ID di Spotify
    user = User.query.filter_by(username=user_info['id']).first()
    
    # Se l'utente non esiste, lo creiamo
    if not user:
        user = User(username=user_info['id'], password=None)
        db.session.add(user)
        db.session.commit()

    # Eseguiamo il login dell'utente
    login_user(user)
    return redirect(url_for('home.homepage'))

# Rotta per il login dell'utente tramite Spotify o credenziali locali
@auth_bp.route('/', methods=['GET', 'POST'])
def loginlocale():
    # Controlliamo se l'utente è già autenticato tramite Spotify
    token_info = session.get('token_info', None)
    
    if token_info:
        # Se c'è un token, usiamo Spotify per ottenere le informazioni dell'utente
        sp = spotipy.Spotify(auth=token_info['access_token'])
        user_info = sp.current_user()

        # Cerchiamo un utente nel nostro database con l'ID di Spotify
        user = User.query.filter_by(username=user_info['id']).first()
        if not user:
            user = User(username=user_info['id'], password=None)
            db.session.add(user)
            db.session.commit()

        # Eseguiamo il login dell'utente
        login_user(user)
        flash("Login avvenuto con successo tramite Spotify!", "success")
        return redirect(url_for('home.homepage'))

    # Se è una richiesta POST (l'utente ha inserito username e password)
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Cerchiamo l'utente nel database
        user = User.query.filter_by(username=username).first()

        # Se l'utente esiste e la password è corretta, facciamo il login
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash("Login avvenuto con successo!", "success")
            return redirect(url_for('home.homepage'))
        
        # Se le credenziali non sono valide, mostriamo un messaggio di errore
        flash("Credenziali non valide.", "error")
    
    # Mostriamo la pagina di login
    return render_template('login.html')
