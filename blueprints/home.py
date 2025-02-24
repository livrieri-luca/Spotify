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

# Route per visualizzare i brani della playlist
@home_bp.route('/playlist_tracks/<playlist_id>')
def playlist_tracks(playlist_id):
    token_info = session.get('token_info', None)
    if not token_info:
        return redirect(url_for('auth.login'))  

    sp = spotipy.Spotify(auth=token_info['access_token'])
    tracks = sp.playlist_tracks(playlist_id)['items']

    return render_template('playlist_tracks.html', tracks=tracks, playlist_id=playlist_id)

# Nuova route per visualizzare i dettagli di un brano (in una pagina separata)
@home_bp.route('/track_details/<track_id>')
def track_details(track_id):
    token_info = session.get('token_info', None)
    if not token_info:
        return redirect(url_for('auth.login'))  

    sp = spotipy.Spotify(auth=token_info['access_token'])
    
    track = sp.track(track_id)
    artist_id = track['artists'][0]['id']
    
    artist_details = sp.artist(artist_id)
    
    # Ottieni la lista dei generi in modo sicuro
    genre = artist_details.get('genres', [])
    
    # Se la lista è vuota, imposta il genere di default
    genre = genre[0] if genre else 'Genere sconosciuto'

    # Ottieni l'ID della playlist dai parametri della query
    playlist_id = request.args.get('playlist_id')

    return render_template('track_details.html', track=track, genre=genre, playlist_id=playlist_id)


