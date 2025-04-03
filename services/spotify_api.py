import spotipy 
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
import pandas as pd

SPOTIFY_CLIENT_ID = "200875a1e6d941bebe8d3ab86bd8dadf"
SPOTIFY_CLIENT_SECRET = "c35e9f794b0e44baaf935f5e8638b320"
SPOTIFY_REDIRECT_URI = "https://5000-livrieriluca-spotify-j2303qzjxsm.ws-eu118.gitpod.io/callback"
SPOTIFY_SCOPE = "user-read-private user-read-email playlist-read-private"

sp_oauth = SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope=SPOTIFY_SCOPE,
    show_dialog=True
)

sp_public = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET
))

def get_spotify_object(token_info=None):
    return spotipy.Spotify(auth=token_info['access_token']) if token_info else sp_public

def get_user_info(token_info):
    return get_spotify_object(token_info).current_user()

def get_user_playlists(token_info):
    return get_spotify_object(token_info).current_user_playlists()['items']

def get_playlist_tracks(token_info, playlist_id):
    try:
        response = get_spotify_object(token_info).playlist_tracks(playlist_id)
        return response.get('items', []) if response else []  # Ritorna un array vuoto se la risposta è vuota o None
    except Exception as e:
        print(f"Errore nel recupero dei brani della playlist {playlist_id}: {e}")
        return []  # Se c'è un errore, ritorna una lista vuota

def get_track_details(token_info, track_id):
    sp = get_spotify_object(token_info)
    track = sp.track(track_id)
    artist_details = sp.artist(track['artists'][0]['id'])
    
    genres = artist_details.get('genres', [])
    if genres:
        genre = genres[0]
    else:
        genre = 'Genere sconosciuto'

    return track, genre

def get_all_tracks(token_info, playlist_id=None):
    sp = get_spotify_object(token_info)
    
    if playlist_id:  # Se viene passato un playlist_id, recupera solo le tracce di quella playlist
        tracks = get_playlist_tracks(token_info, playlist_id)
    else:
        # Se non c'è un playlist_id, recupera tutte le playlist dell'utente
        playlists = get_user_playlists(token_info)
        tracks_data = []
        
        for playlist in playlists:
            playlist_id = playlist['id']
            tracks = get_playlist_tracks(token_info, playlist_id)
            
            # Aggiungi le tracce alla lista
            for track in tracks:
                track_info = track['track']
                release_date = track_info['album'].get('release_date', 'Unknown')
                popularity = track_info['popularity']
                duration_ms = track_info['duration_ms']
                
                tracks_data.append({
                    'track_name': track_info['name'],
                    'artist': track_info['artists'][0]['name'],
                    'album': track_info['album']['name'],
                    'genre': track_info['album'].get('genres', ['Sconosciuto'])[0],
                    'release_date': release_date,
                    'duration_ms': duration_ms,
                    'popularity': popularity
                })
                
        return pd.DataFrame(tracks_data)

    # Se playlist_id è passato, restituisci i dettagli delle tracce per quella playlist
    tracks_data = []
    for track in tracks:
        track_info = track['track']
        release_date = track_info['album'].get('release_date', 'Unknown')
        popularity = track_info['popularity']
        duration_ms = track_info['duration_ms']
        
        tracks_data.append({
            'track_name': track_info['name'],
            'artist': track_info['artists'][0]['name'],
            'album': track_info['album']['name'],
            'genre': track_info['album'].get('genres', ['Sconosciuto'])[0],
            'release_date': release_date,
            'duration_ms': duration_ms,
            'popularity': popularity
        })
    
    return pd.DataFrame(tracks_data)
