from flask import Blueprint, render_template, session, redirect, url_for, request,flash
from flask_login import login_required, current_user
import spotipy
import pandas as pd
import plotly.express as px
from collections import Counter
from services.spotify_api import get_user_info, get_user_playlists, get_all_tracks,get_playlist_tracks,get_public_tracks, get_track_details,SpotifyClientCredentials, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET,get_spotify_object
from models import ListaPlaylist,SavedPlaylist,db
home_bp = Blueprint('home', __name__)

sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET
))


@home_bp.route('/home')
@login_required
def homepage():
    token_info = session.get('token_info')
    spotify_logged_in = bool(token_info)
    user_info = get_user_info(token_info) if spotify_logged_in else None
    playlists = get_user_playlists(token_info) if spotify_logged_in else None
    saved_playlists = SavedPlaylist.query.filter_by(user_id=current_user.id).all()  # Playlist salvate dall'utente
    return render_template('home.html', user_info=user_info, playlists=playlists, saved_playlists=saved_playlists, spotify_logged_in=spotify_logged_in)

# Funzione per recuperare i brani pubblici tramite Spotify API
def get_public_tracks():
    # Recupera i brani più popolari pubblici (modifica la query se necessario)
    tracks = sp.current_user_top_tracks(limit=10)
    return tracks['items']
@home_bp.route('/playlist_tracks/<playlist_id>')
@login_required
def playlist_tracks(playlist_id):
    token_info = session.get('token_info')
    
    # Se non c'è il token e siamo in locale
    if not token_info:
        tracks = EXAMPLE_TRACKS  # Mostra i brani di esempio
        return render_template('playlist_tracks.html', tracks=tracks, playlist_id=playlist_id, message="Accesso Spotify non disponibile, mostrando brani di esempio.")
    
    tracks = get_playlist_tracks(token_info, playlist_id)
    return render_template('playlist_tracks.html', tracks=tracks, playlist_id=playlist_id)


@home_bp.route('/public_tracks')
def show_public_tracks():
    public_tracks = sp.current_user_top_tracks(limit=10)

    if 'items' not in public_tracks:
        return "Errore: Nessuna traccia trovata", 500

    return render_template('playlist_tracks.html', tracks=public_tracks['items'])


@home_bp.route('/track_details/<track_id>')
def track_details(track_id):
    token_info = session.get('token_info')
    track, genre = get_track_details(token_info, track_id)
    playlist_id = request.args.get('playlist_id')
    return render_template('track_details.html', track=track, genre=genre, playlist_id=playlist_id)


def get_playlist_tracks(token_info, playlist_id):
    results = sp.playlist_tracks(playlist_id)
    return results['items']


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

    tracks_df['release_date'] = pd.to_datetime(tracks_df['release_date'], errors='coerce')
    tracks_df['year'] = tracks_df['release_date'].dt.year

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
        return redirect(url_for('auth.login'))

    playlists = get_user_playlists(token_info)

    if request.method == 'POST':
        playlist_id_1 = request.form.get('playlist_id_1')
        playlist_id_2 = request.form.get('playlist_id_2')
        return redirect(url_for('home.confronto_playlist', playlist_id_1=playlist_id_1, playlist_id_2=playlist_id_2))

    return render_template('select_playlists_for_comparison.html', playlists=playlists)


@home_bp.route('/confronto_playlist/<playlist_id_1>/<playlist_id_2>', methods=['GET'])
@login_required
def confronto_playlist(playlist_id_1, playlist_id_2):
    token_info = session.get('token_info')
    if not token_info:
        return redirect(url_for('auth.login'))

    # Ottieni le tracce per entrambe le playlist
    playlist_1_tracks = get_playlist_tracks(token_info, playlist_id_1)
    playlist_2_tracks = get_playlist_tracks(token_info, playlist_id_2)

    # Estrazione dei brani dalle playlist
    tracks_1 = {track['track']['name'] for track in playlist_1_tracks}
    tracks_2 = {track['track']['name'] for track in playlist_2_tracks}
    common_tracks = tracks_1.intersection(tracks_2)
    similarity_percentage = len(common_tracks) / min(len(tracks_1), len(tracks_2)) * 100

    tracks_count = {
        "Playlist 1": len(tracks_1),
        "Playlist 2": len(tracks_2),
        "Brani Comuni": len(common_tracks),
        "Somiglianza (%)": similarity_percentage
    }

    # Creazione del grafico per i brani
    fig_tracks = px.bar(
        x=list(tracks_count.keys()),
        y=list(tracks_count.values()),
        labels={'x': 'Categoria', 'y': 'Numero di Brani'},
        title="Confronto Brani nelle Playlist"
    ).to_html(full_html=False)

    # Estrazione degli artisti comuni nelle playlist
    artists_1 = {track['track']['artists'][0]['name'] for track in playlist_1_tracks}
    artists_2 = {track['track']['artists'][0]['name'] for track in playlist_2_tracks}
    common_artists = artists_1.intersection(artists_2)

    # Conteggio della frequenza degli artisti nelle playlist
    artist_count_1 = {artist: sum(1 for track in playlist_1_tracks if artist in [a['name'] for a in track['track']['artists']]) for artist in common_artists}
    artist_count_2 = {artist: sum(1 for track in playlist_2_tracks if artist in [a['name'] for a in track['track']['artists']]) for artist in common_artists}

    artist_data = pd.DataFrame({
        'Artist': list(common_artists),
        'Playlist 1': [artist_count_1.get(artist, 0) for artist in common_artists],
        'Playlist 2': [artist_count_2.get(artist, 0) for artist in common_artists]
    })

    artist_data_melted = artist_data.melt(id_vars="Artist", value_vars=["Playlist 1", "Playlist 2"],
                                          var_name="Playlist", value_name="Frequenza")

    # Creazione del grafico per gli artisti
    fig_artists = px.bar(
        artist_data_melted,
        x="Artist",
        y="Frequenza",
        color="Playlist",
        labels={'Artist': 'Artista', 'Frequenza': 'Frequenza'},
        title="Artisti in Comune - Frequenza nelle Playlist"
    ).to_html(full_html=False)

    # Estrazione della popolarità per entrambe le playlist
    popularity_1 = [track['track']['popularity'] for track in playlist_1_tracks]
    popularity_2 = [track['track']['popularity'] for track in playlist_2_tracks]
    avg_popularity_1 = sum(popularity_1) / len(popularity_1)
    avg_popularity_2 = sum(popularity_2) / len(popularity_2)

    # Creazione del grafico per la popolarità
    fig_popularity = px.bar(
        x=['Playlist 1', 'Playlist 2'],
        y=[avg_popularity_1, avg_popularity_2],
        labels={'x': 'Playlist', 'y': 'Popolarità Media'},
        title="Confronto Popolarità Media delle Playlist"
    ).to_html(full_html=False)

    # Estrazione dei generi musicali
    genres_1 = [track['track']['artists'][0].get('genres', ['Sconosciuto']) for track in playlist_1_tracks]
    genres_2 = [track['track']['artists'][0].get('genres', ['Sconosciuto']) for track in playlist_2_tracks]

    # Verifica dei generi estratti
    print("Generi Playlist 1:", genres_1)
    print("Generi Playlist 2:", genres_2)

    # Creazione dei contatori per i generi
    genre_count_1 = Counter([genre for sublist in genres_1 for genre in sublist])
    genre_count_2 = Counter([genre for sublist in genres_2 for genre in sublist])

    # Verifica dei contatori
    print("Contatori dei generi Playlist 1:", genre_count_1)
    print("Contatori dei generi Playlist 2:", genre_count_2)

    # Creazione dei dati per il grafico dei generi
    all_genres = set(genre_count_1.keys()).union(genre_count_2.keys())
    genre_frequencies_1 = [genre_count_1.get(genre, 0) for genre in all_genres]
    genre_frequencies_2 = [genre_count_2.get(genre, 0) for genre in all_genres]

    # Creazione del dataframe per i generi
    genre_data = pd.DataFrame({
        'Genre': list(all_genres),
        'Playlist 1': genre_frequencies_1,
        'Playlist 2': genre_frequencies_2
    })

    # Verifica del dataframe
    print("Dati dei generi:", genre_data)

    # Melting dei dati per il grafico
    genre_data_melted = genre_data.melt(id_vars="Genre", value_vars=["Playlist 1", "Playlist 2"],
                                         var_name="Playlist", value_name="Frequency")

    # Creazione del grafico per i generi
    fig_genres = px.bar(
        genre_data_melted,
        x="Genre",
        y="Frequency",
        color="Playlist",
        labels={'Genre': 'Genere', 'Frequency': 'Frequenza'},
        title="Confronto Generi Musicali"
    ).to_html(full_html=False)

    # Renderizzazione dei risultati nella pagina
    return render_template('comparison_results.html', 
                           fig_tracks=fig_tracks, 
                           fig_artists=fig_artists, 
                           fig_popularity=fig_popularity, 
                           fig_genres=fig_genres)


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
        playlists = ListaPlaylist.query.filter(ListaPlaylist.nome.like(f'%{query}%')).all()
        spotify_results = sp.search(q=query, type='playlist', limit=10)
        spotify_playlists = spotify_results.get('playlists', {}).get('items', [])
        return render_template('search.html', playlists=playlists, spotify_playlists=spotify_playlists)

    return render_template('search.html', playlists=None, spotify_playlists=None)

@home_bp.route('/salva_playlist', methods=['POST'])
@login_required
def save_playlist():
    playlist_id = request.form['playlist_id']
    
    # Verifica se la playlist è già stata salvata
    existing_playlist = SavedPlaylist.query.filter_by(user_id=current_user.id, playlist_id=playlist_id).first()

    if not existing_playlist:
        # Se la playlist non è già stata salvata, salvala nel database
        playlist_info = sp.playlist(playlist_id)  # Ottieni i dettagli della playlist
        playlist_name = playlist_info['name']  # Nome della playlist
        
        new_saved_playlist = SavedPlaylist(user_id=current_user.id, playlist_id=playlist_id)
        db.session.add(new_saved_playlist)
        db.session.commit()
        flash("Playlist salvata con successo!", "success")
    else:
        flash("Questa playlist è già stata salvata.", "info")

    # Recupera tutte le playlist salvate per l'utente
    saved_playlists = SavedPlaylist.query.filter_by(user_id=current_user.id).all()
    
    # Ritorna alla ricerca con i messaggi e le playlist salvate
    return redirect(url_for('home.search', message="Playlist salvata con successo!", saved_playlists=saved_playlists))

@home_bp.route('/recommendations', methods=['GET', 'POST'])
@login_required
def recommendations():
    token_info = session.get('token_info')
    if not token_info:
        return redirect(url_for('auth.login'))
    
    sp = get_spotify_object(token_info)
    user_playlists = sp.current_user_playlists()['items']
    
    recommendations = []

    if request.method == 'POST':
        artist_id = request.form.get('artist_id')
        track_id = request.form.get('track_id')
        genre = request.form.get('genre')
        playlist_id = request.form.get('playlist_id')
        create_new_playlist = request.form.get('create_new_playlist')
        new_playlist_name = request.form.get('new_playlist_name')

        # Parametri per ottenere le raccomandazioni
        params = {
            'seed_artists': artist_id if artist_id else '',
            'seed_tracks': track_id if track_id else '',
            'seed_genres': genre if genre else '',
            'limit': 10
        }

        recommendations = sp.recommendations(**params)['tracks']
        track_uris = [track['uri'] for track in recommendations]

        # Creazione di una nuova playlist, se richiesto
        if create_new_playlist and new_playlist_name:
            user_id = sp.current_user()['id']
            new_playlist = sp.user_playlist_create(user_id, new_playlist_name, public=False)
            playlist_id = new_playlist['id']
            flash(f"Nuova playlist '{new_playlist_name}' creata!", 'success')

        # Aggiungi tracce alla playlist selezionata o nuova
        if playlist_id:
            add_tracks_to_playlist(token_info, playlist_id, track_uris)
            flash('Brani aggiunti alla playlist!', 'success')

    return render_template('recommendations.html', recommendations=recommendations, user_playlists=user_playlists)