from flask import Flask, redirect, request, url_for, render_template, session
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Spotify API credentials
SPOTIFY_CLIENT_ID = "200875a1e6d941bebe8d3ab86bd8dadf"
SPOTIFY_CLIENT_SECRET = "c35e9f794b0e44baaf935f5e8638b320"
SPOTIFY_REDIRECT_URI = "https://5000-livrieriluca-spotify-1pzvm0v6wu7.ws-eu117.gitpod.io/callback"  # Redirect URL after login

app = Flask(__name__)
app.secret_key = 'chiave_per_session'  # Secret key for session identification

# Configure SpotifyOAuth for authentication and redirect URI
sp_oauth = SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope="user-read-private user-library-read playlist-read-private",  # Added permission for playlists
    show_dialog=True  # Force the request for new credentials
)

@app.route('/')
def login():
    auth_url = sp_oauth.get_authorize_url()  # Spotify login
    return redirect(auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')  # Get authorization code
    token_info = sp_oauth.get_access_token(code)  # Exchange code for access token
    session['token_info'] = token_info  # Save token to session for later use
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.clear()  # Clear the access token stored in the session
    return redirect(url_for('login'))

@app.route('/home')
def home():
    token_info = session.get('token_info', None)  # Get the token info from session
    if not token_info:
        return redirect(url_for('login'))

    sp = spotipy.Spotify(auth=token_info['access_token'])  # Use the access token to create a Spotify object
    user_info = sp.current_user()  # Get the user profile

    # Get the user's playlists
    playlists = sp.current_user_playlists()['items']

    return render_template('home.html', user_info=user_info, playlists=playlists)  # Pass user info and playlists to template

@app.route('/playlist/<playlist_id>')
def playlist_tracks(playlist_id):
    token_info = session.get('token_info', None)  # Get the token info from session
    sp = spotipy.Spotify(auth=token_info['access_token'])  # Use the access token to create a Spotify object

    # Get the tracks of the specified playlist
    results = sp.playlist_tracks(playlist_id)
    tracks = results['items']  # List of tracks in the playlist

    return render_template('playlist_tracks.html', tracks=tracks)  # Pass the tracks to the playlist_tracks template

if __name__ == '__main__':
    app.run(debug=True)
