from flask import Blueprint, redirect, request, url_for, session, render_template
import spotipy
from services.spotify_oauth import get_spotify_object

home_bp = Blueprint('home', __name__)

@home_bp.route('/home')
def homepage():
    token_info = session.get('token_info', None)

    if token_info:
        sp = get_spotify_object(token_info)
        user_info = sp.current_user()
        playlists = sp.current_user_playlists()['items']
    else:
        user_info = None
        playlists = None  # Nessuna playlist se non autenticato

    return render_template('home.html', user_info=user_info, playlists=playlists)



@home_bp.route('/playlist_tracks/<playlist_id>')
def playlist_tracks(playlist_id):
    token_info = session.get('token_info', None)
    if not token_info:
        return redirect(url_for('auth.login'))  

    sp = spotipy.Spotify(auth=token_info['access_token'])
    tracks = sp.playlist_tracks(playlist_id)['items']

    return render_template('playlist_tracks.html', tracks=tracks)
