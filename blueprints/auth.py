from flask import Blueprint, render_template, redirect, request, url_for, flash, session
from flask_login import login_user, logout_user, login_required
from flask_bcrypt import Bcrypt
from models import db, User
import spotipy
from services.spotify_api import sp_oauth

auth_bp = Blueprint('auth', __name__)
bcrypt = Bcrypt()

@auth_bp.route('/')
def login():
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    token_info = session.get('token_info', None)
    user_info = None

    if token_info:
        sp = spotipy.Spotify(auth=token_info['access_token'])
        user_info = sp.current_user()

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
            return redirect(url_for('auth.login'))

    return render_template('register.html', user_info=user_info)

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home.homepage'))

@auth_bp.route('/callback')
def callback():
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session['token_info'] = token_info
    return redirect(url_for('auth.loginlocale'))

@auth_bp.route('/loginlocale', methods=['GET', 'POST'])
def loginlocale():
    token_info = session.get('token_info', None)
    sp = spotipy.Spotify(auth=token_info['access_token'])
    user_info = sp.current_user()
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('home.homepage'))
        
        return render_template('login.html', error="Credenziali non valide.", user_info=user_info)
    
    return render_template('login.html', error=None, user_info=user_info)

@auth_bp.route('/annullalogin')
def annullalogin():
    try:
        os.remove(".cache")
    except:
        print(".cache non esiste")
    session.clear()
    return redirect(url_for('home.homepage'))
