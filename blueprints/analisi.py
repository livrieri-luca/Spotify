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
    if len(saved_playlists) < 2:
        return "Sono necessarie almeno due playlist per effettuare l'analisi."

    playlist_data = {}
    playlist_names = []

    for i, saved in enumerate(saved_playlists[:2]):
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
            playlist_names.append(f'Playlist {i+1}')

        playlist_data[f'playlist_{i+1}'] = pd.DataFrame(track_info)

    df1, df2 = playlist_data['playlist_1'], playlist_data['playlist_2']
    common_tracks = set(df1['track_name']) & set(df2['track_name'])
    similarity = len(common_tracks) / min(len(df1), len(df2)) * 100 if min(len(df1), len(df2)) > 0 else 0
    similarity_df = pd.DataFrame({
        'Playlist': [playlist_names[0], playlist_names[1], 'Comuni'],
        'Numero Brani': [len(df1), len(df2), len(common_tracks)]
    })
    similarity_chart = px.bar(similarity_df, x='Playlist', y='Numero Brani',
                              title=f'Brani in comune (Somiglianza: {similarity:.2f}%)')

    a1 = df1.explode('artists')['artists']
    a2 = df2.explode('artists')['artists']
    common_artists = set(a1) & set(a2)
    artist_freq = pd.DataFrame({
        'Artista': list(common_artists),
        f'Frequenza {playlist_names[0]}': [a1.tolist().count(a) for a in common_artists],
        f'Frequenza {playlist_names[1]}': [a2.tolist().count(a) for a in common_artists]
    })
    artist_chart = px.bar(artist_freq.melt(id_vars='Artista', var_name='Playlist', value_name='Frequenza'),
                          x='Artista', y='Frequenza', color='Playlist', barmode='group',
                          title='Artisti in comune e frequenze')

    pop_data = pd.DataFrame({
        'Playlist': [playlist_names[0], playlist_names[1]],
        'Popolarità Media': [df1['popularity'].mean(), df2['popularity'].mean()]
    })
    pop_chart = px.bar(pop_data, x='Playlist', y='Popolarità Media', title='Confronto Popolarità Media')

    g1 = df1.explode('genres')['genres']
    g2 = df2.explode('genres')['genres']
    genre_freq = pd.DataFrame({
        'Genere': list(set(g1) | set(g2)),
        playlist_names[0]: [g1.tolist().count(g) for g in set(g1) | set(g2)],
        playlist_names[1]: [g2.tolist().count(g) for g in set(g1) | set(g2)]
    })
    genre_chart = px.bar(genre_freq.melt(id_vars='Genere', var_name='Playlist', value_name='Frequenza'),
                         x='Genere', y='Frequenza', color='Playlist', barmode='group',
                         title='Confronto dei Generi Musicali')

    df1['release_year'] = pd.to_numeric(df1['release_year'], errors='coerce')
    df2['release_year'] = pd.to_numeric(df2['release_year'], errors='coerce')
    year_df = pd.concat([
        df1[['release_year']].assign(Playlist=playlist_names[0]),
        df2[['release_year']].assign(Playlist=playlist_names[1])
    ])
    time_chart = px.histogram(year_df, x='release_year', color='Playlist', barmode='overlay',
                              title='Distribuzione Temporale dei Brani')

    combined_df = pd.concat([df1, df2])

    top_artists = combined_df.explode('artists')['artists'].value_counts().head(5).reset_index()
    top_artists.columns = ['Artista', 'Occorrenze']
    top_artists_chart = px.bar(top_artists, x='Artista', y='Occorrenze', title='Top 5 Artisti Più Presenti')

    top_albums = combined_df['album'].value_counts().head(5).reset_index()
    top_albums.columns = ['Album', 'Occorrenze']
    top_albums_chart = px.bar(top_albums, x='Album', y='Occorrenze', title='Top 5 Album Più Presenti')

    top_genres = combined_df.explode('genres')['genres'].value_counts().head(5).reset_index()
    top_genres.columns = ['Genere', 'Occorrenze']
    top_genres_chart = px.pie(top_genres, names='Genere', values='Occorrenze', title='Top 5 Generi Musicali')

    return render_template(
        'analisi.html',
        similarity_chart=similarity_chart.to_html(full_html=False),
        artist_chart=artist_chart.to_html(full_html=False),
        pop_chart=pop_chart.to_html(full_html=False),
        genre_chart=genre_chart.to_html(full_html=False),
        time_chart=time_chart.to_html(full_html=False),
        top_artists_chart=top_artists_chart.to_html(full_html=False),
        top_albums_chart=top_albums_chart.to_html(full_html=False),
        top_genres_chart=top_genres_chart.to_html(full_html=False),
        playlist_names=playlist_names
    )