from flask import Blueprint, redirect, request, url_for, session, render_template
from services.spotify_api import get_user_info, get_user_playlists, get_playlist_tracks, get_track_details, get_all_tracks
import plotly.express as px

home_bp = Blueprint('home', __name__)

@home_bp.route('/home')
def homepage():
    token_info = session.get('token_info')
    user_info = get_user_info(token_info) if token_info else None
    playlists = get_user_playlists(token_info) if token_info else None
    return render_template('home.html', user_info=user_info, playlists=playlists)

@home_bp.route('/playlist_tracks/<playlist_id>')
def playlist_tracks(playlist_id):
    token_info = session.get('token_info')
    if not token_info:
        return redirect(url_for('auth.login'))
    tracks = get_playlist_tracks(token_info, playlist_id)
    return render_template('playlist_tracks.html', tracks=tracks, playlist_id=playlist_id)

@home_bp.route('/track_details/<track_id>')
def track_details(track_id):
    token_info = session.get('token_info')
    if not token_info:
        return redirect(url_for('auth.login'))
    track, genre = get_track_details(token_info, track_id)
    playlist_id = request.args.get('playlist_id')
    return render_template('track_details.html', track=track, genre=genre, playlist_id=playlist_id)

@home_bp.route('/analisi')
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
