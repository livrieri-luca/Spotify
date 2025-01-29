from flask import Flask, redirect, request, url_for, render_template,session
import spotipy
from spotipy.oauth2 import SpotifyOAuth
#le tue credenziali le trovi nella dashboard di prima
SPOTIFY_CLIENT_ID = "200875a1e6d941bebe8d3ab86bd8dadf"
SPOTIFY_CLIENT_SECRET = "c35e9f794b0e44baaf935f5e8638b320"
SPOTIFY_REDIRECT_URI = "https://5000-livrieriluca-spotify-gpl38m12aac.ws-eu117.gitpod.io/callback" #dopo il login andiamo qui

app = Flask(__name__)
app.secret_key = 'chiave_per_session' #ci serve per identificare la sessione

#config SpotifyOAuth per l'autenticazione e redirect uri
sp_oauth = SpotifyOAuth(
client_id=SPOTIFY_CLIENT_ID,
client_secret=SPOTIFY_CLIENT_SECRET,
redirect_uri=SPOTIFY_REDIRECT_URI,
)
scope="user-read-private" #permessi x informazioni dell'utente
@app.route('/')
def login():
    auth_url = sp_oauth.get_authorize_url() #login di spotify
    return redirect(auth_url)
@app.route('/callback')
def callback():
    code = request.args.get('code') #recupero codice di autorizzazione
    token_info = sp_oauth.get_access_token(code) #uso il code per un codice di accesso
    session['token_info'] = token_info #salvo il token nella mia sessione x riutilizzarlo
    return redirect(url_for('home'))
@app.route('/home')
def home():
    token_info = session.get('token_info', None) #recupero token sissione (salvato prima)
    if not token_info:
      return redirect(url_for('login'))
    sp = spotipy.Spotify(auth=token_info['access_token']) #usiamo il token per ottenere i dati del profilo
    user_info = sp.current_user()
    print(user_info) #capiamo la struttura di user_info per usarle nel frontend
    return render_template('home.html', user_info=user_info) #passo le info utente all'home.html
if __name__ == '__main__': #debug
    app.run(debug=True) 
   