from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
import spotipy
import pandas as pd
import plotly.express as px
from services.spotify_api import sp_public
from models import db, SavedPlaylist

analisi_bp = Blueprint('analisi', __name__)
sp = sp_public

def get_track_details(track_id):
    try:
        track = sp.track(track_id)
        artist_ids = [artist['id'] for artist in track['artists'] if artist.get('id')]
        artists_data = sp.artists(artist_ids)['artists'] if artist_ids else []
        genres = {genre for artist in artists_data for genre in artist.get('genres', [])}

        return {
            'track_id': track_id,
            'track_name': track.get('name', 'Traccia sconosciuta'),
            'artists': [a.get('name', 'Sconosciuto') for a in track.get('artists', [])],
            'album': track.get('album', {}).get('name', 'Album sconosciuto'),
            'genres': list(genres),
            'popularity': track.get('popularity', 0),
            'release_year': track.get('album', {}).get('release_date', '1900')[:4]
        }
    except Exception as e:
        print(f"Errore recuperando dettagli per {track_id}: {e}")
        return {}

@analisi_bp.route('/playlist_analysis')
@login_required
def playlist_analysis():
    saved_playlists = SavedPlaylist.query.filter_by(user_id=current_user.id).all()
    if not saved_playlists:
        return "Nessuna playlist trovata per l'utente."

    playlist_data = {}
    playlist_names = []

    for i, saved in enumerate(saved_playlists):
        playlist_id = saved.playlist_id
        track_info = []

        try:
            playlist_metadata = sp.playlist(playlist_id)
            playlist_name = playlist_metadata.get('name', f'Playlist {i+1}')
            playlist_names.append(playlist_name)

            tracks = playlist_metadata['tracks']['items']
            for item in tracks:
                track = item.get('track')
                if track and track.get('id'):
                    details = get_track_details(track['id'])
                    if details:
                        track_info.append(details)
        except Exception as e:
            print(f"Errore con playlist {playlist_id}: {e}")
            playlist_names.append(f'Playlist {i+1} (Errore)')

        playlist_data[playlist_names[-1]] = pd.DataFrame(track_info)

    # Combina tutti i dati
    combined_df = pd.concat(playlist_data.values(), keys=playlist_data.keys(), names=['Playlist']).reset_index(level='Playlist')

    # Matrice di similarità solo se ci sono almeno 2 playlist
    if len(playlist_data) > 1:
        similarity_matrix = pd.DataFrame(index=playlist_names, columns=playlist_names)

        for name1 in playlist_names:
            for name2 in playlist_names:
                df1 = playlist_data[name1]
                df2 = playlist_data[name2]
                common = set(df1['track_name']) & set(df2['track_name'])
                sim = len(common) / min(len(df1), len(df2)) * 100 if min(len(df1), len(df2)) > 0 else 0
                similarity_matrix.loc[name1, name2] = round(sim, 2)

        similarity_chart = px.imshow(
            similarity_matrix.astype(float),
            text_auto=True,
            labels=dict(x="Playlist", y="Playlist", color="Somiglianza (%)"),
            title="Matrice di Similarità tra Playlist"
        ).to_html(full_html=False)
    else:
        similarity_chart = "<p>Solo una playlist disponibile: impossibile calcolare somiglianze.</p>"

    # Popolarità media
    pop_data = combined_df.groupby('Playlist')['popularity'].mean().reset_index()
    pop_chart = px.bar(pop_data, x='Playlist', y='popularity', title='Popolarità Media per Playlist')

    # Distribuzione temporale
    combined_df['release_year'] = pd.to_numeric(combined_df['release_year'], errors='coerce')
    time_chart = px.histogram(combined_df, x='release_year', color='Playlist', barmode='overlay',
                              title='Distribuzione Temporale dei Brani')

    # Generi
    genre_df = combined_df.explode('genres')
    genre_freq = genre_df.groupby(['genres', 'Playlist']).size().reset_index(name='Frequenza')
    genre_chart = px.bar(genre_freq, x='genres', y='Frequenza', color='Playlist',
                         barmode='group', title='Confronto dei Generi Musicali')

    # Artisti
    artist_df = combined_df.explode('artists')
    artist_freq = artist_df.groupby(['artists', 'Playlist']).size().reset_index(name='Frequenza')
    artist_chart = px.bar(artist_freq, x='artists', y='Frequenza', color='Playlist',
                          title='Artisti per Playlist', barmode='group')

    # Top Artisti Globali
    top_artists = artist_df['artists'].value_counts().head(5).reset_index()
    top_artists.columns = ['Artista', 'Occorrenze']
    top_artists_chart = px.bar(top_artists, x='Artista', y='Occorrenze', title='Top 5 Artisti Globali')

    # Top Album Globali
    top_albums = combined_df['album'].value_counts().head(5).reset_index()
    top_albums.columns = ['Album', 'Occorrenze']
    top_albums_chart = px.bar(top_albums, x='Album', y='Occorrenze', title='Top 5 Album Globali')

    # Top Generi Globali
    top_genres = genre_df['genres'].value_counts().head(5).reset_index()
    top_genres.columns = ['Genere', 'Occorrenze']
    top_genres_chart = px.pie(top_genres, names='Genere', values='Occorrenze', title='Top 5 Generi Globali')

    return render_template(
    'analisi.html',
    similarity_chart=similarity_chart,
    artist_chart=artist_chart.to_html(full_html=False) if artist_chart else None,
    pop_chart=pop_chart.to_html(full_html=False) if pop_chart else None,
    genre_chart=genre_chart.to_html(full_html=False) if genre_chart else None,
    time_chart=time_chart.to_html(full_html=False) if time_chart else None,
    top_artists_chart=top_artists_chart.to_html(full_html=False) if top_artists_chart else None,
    top_albums_chart=top_albums_chart.to_html(full_html=False) if top_albums_chart else None,
    top_genres_chart=top_genres_chart.to_html(full_html=False) if top_genres_chart else None,
    playlist_names=playlist_names
)

