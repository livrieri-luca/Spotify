from flask import Blueprint, redirect, request, url_for, session, render_template
from services.spotify_api import get_spotify_object, get_user_info, get_user_playlists, get_playlist_tracks, get_track_details,get_all_tracks
import plotly.express as px

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
@home_bp.route('/analisi')
def analytics():
    token_info = session.get('token_info', None)
    
    if not token_info:
        return redirect(url_for('auth.login'))

    # Raccogli i dati dei brani
    tracks_df = get_all_tracks(token_info)

    # Debug: controlla che il DataFrame contenga i dati
    print("Tracks DataFrame:", tracks_df.head())  # Visualizza i primi 5 record

    # Top 5 artisti più presenti
    top_artists = tracks_df['artist'].value_counts().head(5)
    
    # Crea il grafico a barre per i Top 5 Artisti
    fig1 = px.bar(top_artists, x=top_artists.index, y=top_artists.values, 
                  labels={'x': 'Artista', 'y': 'Numero di brani'}, 
                  title="Top 5 Artisti più presenti")

    # Top 5 album più presenti
    top_albums = tracks_df['album'].value_counts().head(5)
    
    # Crea il grafico a torta per i Top 5 Album
    fig2 = px.pie(top_albums, names=top_albums.index, values=top_albums.values, 
                  title="Top 5 Album più presenti")

    # Distribuzione dei generi
    genre_distribution = tracks_df['genre'].value_counts()
    
    # Crea il grafico a torta per la Distribuzione dei Generi
    fig3 = px.pie(genre_distribution, names=genre_distribution.index, values=genre_distribution.values, 
                  title="Distribuzione dei Generi Musicali")

    # Rendi i grafici HTML
    fig_artists_html = fig1.to_html(full_html=False)  # Non include l'intero HTML
    fig_albums_html = fig2.to_html(full_html=False)
    fig_genres_html = fig3.to_html(full_html=False)

    return render_template('analytics.html', 
                           fig_artists=fig_artists_html, 
                           fig_albums=fig_albums_html, 
                           fig_genres=fig_genres_html)