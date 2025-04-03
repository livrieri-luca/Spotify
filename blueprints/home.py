from flask import Blueprint, render_template, session, redirect, url_for, request
from flask_login import login_required, current_user
import spotipy
import pandas as pd
import plotly.express as px
from services.spotify_api import get_user_info, get_user_playlists, get_all_tracks, get_playlist_tracks, get_track_details, SpotifyClientCredentials, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET
from models import ListaPlaylist

home_bp = Blueprint('home', __name__)

# Creazione dell'istanza di Spotipy con le credenziali client (senza login utente)
sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET
))

@home_bp.route('/home')
@login_required
def homepage():
    token_info = session.get('token_info')
    spotify_logged_in = bool(token_info)
    
    user_info = None
    playlists = None

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
def track_details(track_id):
    token_info = session.get('token_info')
    track, genre = get_track_details(token_info, track_id)
    playlist_id = request.args.get('playlist_id')
    return render_template('track_details.html', track=track, genre=genre, playlist_id=playlist_id)

@home_bp.route('/analisi')
@login_required
def analytics():
    token_info = session.get('token_info')
    if not token_info:
        return redirect(url_for('auth.login'))

    # Recupera i dati delle tracce
    tracks_df = get_all_tracks(token_info)

    # Parte per la visualizzazione dei Top 5 Artisti e Album
    top_artists = tracks_df['artist'].value_counts().head(5)
    fig_artists_html = px.bar(top_artists, x=top_artists.index, y=top_artists.values, 
                              labels={'x': 'Artista', 'y': 'Numero di brani'}, 
                              title="Top 5 Artisti più presenti").to_html(full_html=False)
    
    top_albums = tracks_df['album'].value_counts().head(5)
    fig_albums_html = px.pie(top_albums, names=top_albums.index, values=top_albums.values, 
                             title="Top 5 Album più presenti").to_html(full_html=False)

    # Aggiungi la parte per l'analisi temporale, durata, popolarità, ecc.
    tracks_df['release_date'] = pd.to_datetime(tracks_df['release_date'], errors='coerce')
    tracks_df['year'] = tracks_df['release_date'].dt.year

    # Grafici delle distribuzioni
    year_counts = tracks_df['year'].value_counts().sort_index()
    fig_years_html = px.bar(year_counts, x=year_counts.index, y=year_counts.values,
                            labels={'x': 'Anno', 'y': 'Numero di brani'},
                            title='Distribuzione Temporale dei Brani').to_html(full_html=False)

    fig_dur_html = px.histogram(tracks_df, x='duration_ms', nbins=30,
                                title='Distribuzione della Durata dei Brani').to_html(full_html=False)

    fig_pop_html = px.histogram(tracks_df, x='popularity', nbins=20,
                                title='Distribuzione della Popolarità').to_html(full_html=False)

    genre_counts = tracks_df['genre'].value_counts().head(10)
    fig_genres_html = px.bar(genre_counts, x=genre_counts.index, y=genre_counts.values,
                             labels={'x': 'Genere', 'y': 'Numero di brani'},
                             title='Distribuzione dei Generi Musicali').to_html(full_html=False)

    pop_time_df = tracks_df.groupby('year')['popularity'].mean().reset_index()
    fig_pop_time_html = px.line(pop_time_df, x='year', y='popularity',
                                title='Evoluzione della Popolarità nel Tempo').to_html(full_html=False)

    # Confronto tra playlist
    playlist_id_1 = request.args.get('playlist_id_1')
    playlist_id_2 = request.args.get('playlist_id_2')

    if playlist_id_1 and playlist_id_2:
        tracks_1 = get_all_tracks(token_info, playlist_id_1)
        tracks_2 = get_all_tracks(token_info, playlist_id_2)

        # Trova i brani in comune
        tracks_1_ids = {track['track_id'] for track in tracks_1}
        tracks_2_ids = {track['track_id'] for track in tracks_2}
        common_tracks = tracks_1_ids.intersection(tracks_2_ids)
        total_tracks = min(len(tracks_1), len(tracks_2))
        similarity_percentage = (len(common_tracks) / total_tracks) * 100 if total_tracks > 0 else 0

        # Confronto dei generi tra playlist
        genres_1 = {track['genre'] for track in tracks_1}
        genres_2 = {track['genre'] for track in tracks_2}
        common_genres = genres_1.intersection(genres_2)

        # Calcolare la popolarità media di entrambe le playlist
        avg_pop_1 = sum(track['popularity'] for track in tracks_1) / len(tracks_1) if tracks_1 else 0
        avg_pop_2 = sum(track['popularity'] for track in tracks_2) / len(tracks_2) if tracks_2 else 0

        # Confronto dei generi musicali
        genres_comparison = pd.DataFrame({
            'Genere': list(common_genres),
            'Playlist 1': [sum(1 for track in tracks_1 if track['genre'] == genre) for genre in common_genres],
            'Playlist 2': [sum(1 for track in tracks_2 if track['genre'] == genre) for genre in common_genres]
        })

        fig_genres_comparison = px.bar(genres_comparison, x='Genere', y=['Playlist 1', 'Playlist 2'],
                                       title='Confronto dei Generi Musicali tra Playlist',
                                       labels={'value': 'Numero di brani'}).to_html(full_html=False)

        # Confronto della popolarità media delle playlist
        pop_comparison = pd.DataFrame({
            'Playlist': ['Playlist 1', 'Playlist 2'],
            'Popolarità Media': [avg_pop_1, avg_pop_2]
        })

        fig_pop_comparison = px.bar(pop_comparison, x='Playlist', y='Popolarità Media', 
                                    title='Confronto della Popolarità Media tra Playlist',
                                    labels={'Popolarità Media': 'Popolarità Media'}).to_html(full_html=False)

        # Crea il grafico di confronto tra brani
        fig_comparison = px.bar(
            x=['Playlist 1', 'Playlist 2', 'Brani in comune'],
            y=[len(tracks_1), len(tracks_2), len(common_tracks)],
            labels={'x': 'Playlist', 'y': 'Numero di brani'},
            title=f'Confronto brani in comune: {round(similarity_percentage, 2)}% di somiglianza'
        ).to_html(full_html=False)

        # Grafico confronto degli artisti
        artists_1 = {track['artist'] for track in tracks_1}
        artists_2 = {track['artist'] for track in tracks_2}
        common_artists = artists_1.intersection(artists_2)

        fig_artists_comparison = px.bar(
            x=list(common_artists),
            y=[sum(1 for track in tracks_1 if track['artist'] == artist) for artist in common_artists],
            labels={'x': 'Artisti', 'y': 'Numero di brani'},
            title='Artisti in comune'
        ).to_html(full_html=False)

        return render_template('analytics.html',
                               fig_artists=fig_artists_html,
                               fig_albums=fig_albums_html,
                               fig_years=fig_years_html,
                               fig_dur=fig_dur_html,
                               fig_pop=fig_pop_html,
                               fig_genres=fig_genres_html,
                               fig_pop_time=fig_pop_time_html,
                               fig_comparison=fig_comparison,
                               fig_artists_comparison=fig_artists_comparison,
                               fig_genres_comparison=fig_genres_comparison,
                               fig_pop_comparison=fig_pop_comparison,
                               common_tracks=common_tracks,
                               common_artists=common_artists,
                               common_genres=common_genres,
                               similarity_percentage=similarity_percentage,
                               avg_pop_1=avg_pop_1,
                               avg_pop_2=avg_pop_2)
    return render_template('analytics.html',
                           fig_artists=fig_artists_html,
                           fig_albums=fig_albums_html,
                           fig_years=fig_years_html,
                           fig_dur=fig_dur_html,
                           fig_pop=fig_pop_html,
                           fig_genres=fig_genres_html,
                           fig_pop_time=fig_pop_time_html)



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

        # Aggiungi la ricerca delle playlist pubbliche da Spotify
        spotify_results = sp.search(q=query, type='playlist', limit=10)
        spotify_playlists = spotify_results.get('playlists', {}).get('items', [])

        return render_template('search.html', playlists=playlists, spotify_playlists=spotify_playlists)

    # Se la query è vuota, ritorna il template con nessun risultato
    return render_template('search.html', playlists=None, spotify_playlists=None)

@home_bp.route('/salva_playlist', methods=['POST'])
@login_required
def save_playlist():
    playlist_id = request.form['playlist_id']
    playlist = ListaPlaylist.query.get_or_404(playlist_id)
    user_id = current_user.id

    if not playlist_is_saved(user_id, playlist_id):
        new_saved_playlist = SavedPlaylist(user_id=user_id, playlist_id=playlist.id)
        db.session.add(new_saved_playlist)
        db.session.commit()

    return redirect(url_for('home.homepage'))

