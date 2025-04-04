from flask import Blueprint, render_template, session, redirect, url_for, request
from flask_login import login_required, current_user
import spotipy
import pandas as pd
import plotly.express as px
from collections import Counter
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
        return redirect(url_for('home.show_public_tracks'))
    
    tracks = get_playlist_tracks(token_info, playlist_id)

    # Check the structure of the tracks
    print("Tracks retrieved:", tracks)

    return render_template('playlist_tracks.html', tracks=tracks, playlist_id=playlist_id)
# Funzione per ottenere le tracce pubbliche
@home_bp.route('/public_tracks')
def show_public_tracks():
    # Ottieni le tracce top dell'utente
    public_tracks = sp.current_user_top_tracks(limit=10)

    # Assicurati che la risposta contenga le tracce
    if 'items' not in public_tracks:
        return "Errore: Nessuna traccia trovata", 500

    # Passa i dati al template
    return render_template('playlist_tracks.html', tracks=public_tracks['items'])
@home_bp.route('/track_details/<track_id>')
def track_details(track_id):
    token_info = session.get('token_info')
    track, genre = get_track_details(token_info, track_id)
    playlist_id = request.args.get('playlist_id')
    return render_template('track_details.html', track=track, genre=genre, playlist_id=playlist_id)
def get_playlist_tracks(token_info, playlist_id):
    results = sp.playlist_tracks(playlist_id)
    tracks = results['items']  # This assumes 'items' contains the track data

    # Ensure every track has a 'duration_ms' field
    for track in tracks:
        if 'track' in track:
            print(track['track'].get('duration_ms'))  # To check if 'duration_ms' exists

    return tracks

@home_bp.route('/analisi')
@login_required
def analytics():
    token_info = session.get('token_info')
    if not token_info:
        return redirect(url_for('auth.login'))  # Ritorna al login se non autenticato

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

    # Passa tutte le informazioni al template senza il confronto delle playlist
    return render_template('analytics.html',
                           fig_artists=fig_artists_html,
                           fig_albums=fig_albums_html,
                           fig_years=fig_years_html,
                           fig_dur=fig_dur_html,
                           fig_pop=fig_pop_html,
                           fig_genres=fig_genres_html,
                           fig_pop_time=fig_pop_time_html)
 

@home_bp.route('/seleziona_playlist_confronto', methods=['GET', 'POST'])
@login_required
def select_playlists_for_comparison():
    token_info = session.get('token_info')
    if not token_info:
        return redirect(url_for('auth.login'))  # Se non autenticato, reindirizza al login

    # Ottieni le playlist dell'utente da Spotify
    playlists = get_user_playlists(token_info)

    if request.method == 'POST':
        # Prendi gli ID delle playlist selezionate
        playlist_id_1 = request.form.get('playlist_id_1')
        playlist_id_2 = request.form.get('playlist_id_2')

        # Redirect alla pagina di confronto passando gli ID delle playlist
        return redirect(url_for('home.confronto_playlist', playlist_id_1=playlist_id_1, playlist_id_2=playlist_id_2))

    return render_template('select_playlists_for_comparison.html', playlists=playlists)


@home_bp.route('/confronto_playlist/<playlist_id_1>/<playlist_id_2>', methods=['GET'])
@login_required
def confronto_playlist(playlist_id_1, playlist_id_2):
    token_info = session.get('token_info')
    if not token_info:
        return redirect(url_for('auth.login'))  # Se non autenticato, reindirizza al login

    # Ottieni i brani delle due playlist
    playlist_1_tracks = get_playlist_tracks(token_info, playlist_id_1)
    playlist_2_tracks = get_playlist_tracks(token_info, playlist_id_2)

    # --- 1. Confronto Brani in comune ---
    tracks_1 = {track['track']['name'] for track in playlist_1_tracks}
    tracks_2 = {track['track']['name'] for track in playlist_2_tracks}
    common_tracks = tracks_1.intersection(tracks_2)
    similarity_percentage = len(common_tracks) / min(len(tracks_1), len(tracks_2)) * 100

    # Grafico per Brani in comune
    tracks_count = {
        "Playlist 1": len(tracks_1),
        "Playlist 2": len(tracks_2),
        "Brani Comuni": len(common_tracks),
        "Somiglianza (%)": similarity_percentage
    }
    fig_tracks = px.bar(
        x=list(tracks_count.keys()),
        y=list(tracks_count.values()),
        labels={'x': 'Categoria', 'y': 'Numero di Brani'},
        title="Confronto Brani nelle Playlist"
    ).to_html(full_html=False)

    # --- 2. Confronto degli Artisti in comune ---
    artists_1 = {track['track']['artists'][0]['name'] for track in playlist_1_tracks}
    artists_2 = {track['track']['artists'][0]['name'] for track in playlist_2_tracks}
    common_artists = artists_1.intersection(artists_2)

    artist_count_1 = {artist: sum(1 for track in playlist_1_tracks if artist in [a['name'] for a in track['track']['artists']]) for artist in common_artists}
    artist_count_2 = {artist: sum(1 for track in playlist_2_tracks if artist in [a['name'] for a in track['track']['artists']]) for artist in common_artists}

    # Creazione del DataFrame per il grafico degli artisti
    artist_data = pd.DataFrame({
        'Artist': list(common_artists),
        'Playlist 1': [artist_count_1.get(artist, 0) for artist in common_artists],
        'Playlist 2': [artist_count_2.get(artist, 0) for artist in common_artists]
    })

    # Grafico per Artisti in comune
    artist_data_melted = artist_data.melt(id_vars="Artist", value_vars=["Playlist 1", "Playlist 2"],
                                          var_name="Playlist", value_name="Frequenza")

    fig_artists = px.bar(
        artist_data_melted,
        x="Artist",
        y="Frequenza",
        color="Playlist",
        labels={'Artist': 'Artista', 'Frequenza': 'Frequenza'},
        title="Artisti in Comune - Frequenza nelle Playlist"
    ).to_html(full_html=False)

    # --- 3. Confronto della Popolarità Media ---
    popularity_1 = [track['track']['popularity'] for track in playlist_1_tracks]
    popularity_2 = [track['track']['popularity'] for track in playlist_2_tracks]
    avg_popularity_1 = sum(popularity_1) / len(popularity_1)
    avg_popularity_2 = sum(popularity_2) / len(popularity_2)

    # Grafico per Popolarità Media
    fig_popularity = px.bar(
        x=['Playlist 1', 'Playlist 2'],
        y=[avg_popularity_1, avg_popularity_2],
        labels={'x': 'Playlist', 'y': 'Popolarità Media'},
        title="Confronto Popolarità Media delle Playlist"
    ).to_html(full_html=False)

    # --- 4. Confronto dei Generi Musicali ---
    genres_1 = [track['track']['artists'][0].get('genres', []) for track in playlist_1_tracks]
    genres_2 = [track['track']['artists'][0].get('genres', []) for track in playlist_2_tracks]

    genre_count_1 = Counter([genre for sublist in genres_1 for genre in sublist])
    genre_count_2 = Counter([genre for sublist in genres_2 for genre in sublist])

    all_genres = set(genre_count_1.keys()).union(genre_count_2.keys())
    genre_frequencies_1 = [genre_count_1.get(genre, 0) for genre in all_genres]
    genre_frequencies_2 = [genre_count_2.get(genre, 0) for genre in all_genres]

    # Creazione del DataFrame per i generi
    genre_data = pd.DataFrame({
        'Genre': list(all_genres),
        'Playlist 1': genre_frequencies_1,
        'Playlist 2': genre_frequencies_2
    })

    # Melting del DataFrame per trasformarlo in una forma lunga
    genre_data_melted = genre_data.melt(id_vars="Genre", value_vars=["Playlist 1", "Playlist 2"],
                                         var_name="Playlist", value_name="Frequency")

    # Creazione del grafico a barre
    fig_genres = px.bar(
        genre_data_melted,
        x="Genre",
        y="Frequency",
        color="Playlist",
        labels={'Genre': 'Genere', 'Frequency': 'Frequenza'},
        title="Confronto Generi Musicali"
    ).to_html(full_html=False)

    return render_template('comparison_results.html', fig_tracks=fig_tracks, fig_artists=fig_artists, fig_popularity=fig_popularity, fig_genres=fig_genres)


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

