from flask import Blueprint, render_template, session, redirect, url_for,request
from flask_login import login_required
from services.spotify_api import get_user_info, get_user_playlists,get_all_tracks,get_spotify_object,get_playlist_tracks,get_track_details
import plotly.express as px
home_bp = Blueprint('home', __name__)
from models import ListaPlaylist  
@home_bp.route('/home')
@login_required
def homepage():
    token_info = session.get('token_info')
    
    # Se l'utente ha effettuato il login con Spotify
    spotify_logged_in = bool(token_info)
    
    user_info = None
    playlists = None

    # Se l'utente è loggato con Spotify, ottieni le informazioni e le playlist
    if spotify_logged_in:
        user_info = get_user_info(token_info)
        playlists = get_user_playlists(token_info)

    return render_template('home.html', user_info=user_info, playlists=playlists, spotify_logged_in=spotify_logged_in)


@home_bp.route('/playlist_tracks/<playlist_id>')
@login_required
def playlist_tracks(playlist_id):
    token_info = session.get('token_info')
    if not token_info:
        return redirect(url_for('auth.login'))
    tracks = get_playlist_tracks(token_info, playlist_id)
    return render_template('playlist_tracks.html', tracks=tracks, playlist_id=playlist_id)

@home_bp.route('/track_details/<track_id>')
@login_required
def track_details(track_id):
    token_info = session.get('token_info')
    if not token_info:
        return redirect(url_for('auth.login'))
    track, genre = get_track_details(token_info, track_id)
    playlist_id = request.args.get('playlist_id')
    return render_template('track_details.html', track=track, genre=genre, playlist_id=playlist_id)

@home_bp.route('/analisi')
@login_required
def analytics():
    token_info = session.get('token_info')
    if not token_info:
        return redirect(url_for('auth.login'))

    tracks_df = get_all_tracks(token_info)
    
    top_artists = tracks_df['artist'].value_counts().head(5)
    fig_artists_html = px.bar(top_artists, x=top_artists.index, y=top_artists.values, 
                              labels={'x': 'Artista', 'y': 'Numero di brani'}, 
                              title="Top 5 Artisti più presenti").to_html(full_html=False)
    
    top_albums = tracks_df['album'].value_counts().head(5)
    fig_albums_html = px.pie(top_albums, names=top_albums.index, values=top_albums.values, 
                             title="Top 5 Album più presenti").to_html(full_html=False)

    return render_template('analytics.html', 
                           fig_artists=fig_artists_html, 
                           fig_albums=fig_albums_html)

@home_bp.route('/rimuovi/<id>')
def rimuovi(id):
    elemento = ListaPlaylist.query.get_or_404(id)
    db.session.delete(elemento)
    db.session.commit()
    return redirect(url_for('home.homepage'))
@home_bp.route('/search', methods=['GET'])
@login_required
def search():
    query = request.args.get('query')
    
    if query:
        # Ricerca per nome della playlist nel database usando ListaPlaylist
        playlists = ListaPlaylist.query.filter(ListaPlaylist.nome.like(f'%{query}%')).all()
        return render_template('search_results.html', playlists=playlists)
@home_bp.route('/salva_playlist', methods=['POST'])
@login_required
def save_playlist():
    playlist_id = request.form['playlist_id']
    # Trova la playlist o crea una nuova voce nel DB
    playlist = Playlist.query.get_or_404(playlist_id)
    user_id = current_user.id

    # Salva la playlist nel database (per un account locale)
    if not playlist_is_saved(user_id, playlist_id):
        new_saved_playlist = SavedPlaylist(user_id=user_id, playlist_id=playlist.id)
        db.session.add(new_saved_playlist)
        db.session.commit()

    return redirect(url_for('home.homepage'))
