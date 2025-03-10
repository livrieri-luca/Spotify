from flask import Blueprint, redirect, request, url_for, session, render_template
from services.spotify_oauth import get_spotify_object, get_user_info, get_user_playlists, get_playlist_tracks, get_track_details

home_bp = Blueprint('home', __name__)

@home_bp.route('/home')
def homepage():
    token_info = session.get('token_info', None)

    if token_info:
        user_info = get_user_info(token_info)
        playlists = get_user_playlists(token_info)
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

    tracks = get_playlist_tracks(token_info, playlist_id)

    return render_template('playlist_tracks.html', tracks=tracks, playlist_id=playlist_id)

# Nuova route per visualizzare i dettagli di un brano (in una pagina separata)
@home_bp.route('/track_details/<track_id>')
def track_details(track_id):
    token_info = session.get('token_info', None)
    if not token_info:
        return redirect(url_for('auth.login'))

    track, genre = get_track_details(token_info, track_id)

    # Ottieni l'ID della playlist dai parametri della query
    playlist_id = request.args.get('playlist_id')

    return render_template('track_details.html', track=track, genre=genre, playlist_id=playlist_id)
