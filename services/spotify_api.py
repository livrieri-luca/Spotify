
import spotipy 
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
import pandas as pd

SPOTIFY_CLIENT_ID = "200875a1e6d941bebe8d3ab86bd8dadf"
SPOTIFY_CLIENT_SECRET = "c35e9f794b0e44baaf935f5e8638b320"
SPOTIFY_REDIRECT_URI = "https://5000-livrieriluca-spotify-ti646n8663u.ws-eu118.gitpod.io/callback"
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
    return get_spotify_object(token_info).playlist_tracks(playlist_id)['items']
def get_track_details(token_info, track_id):
    sp = get_spotify_object(token_info)
    track = sp.track(track_id)
    artist_details = sp.artist(track['artists'][0]['id'])
    
    # Verifica se la lista dei generi è vuota prima di accedere
    genres = artist_details.get('genres', [])
    if genres:
        genre = genres[0]  # Prendi il primo genere se la lista non è vuota
    else:
        genre = 'Genere sconosciuto'  # Fallback se la lista è vuota

    return track, genre

def get_all_tracks(token_info):
    sp = get_spotify_object(token_info)
    playlists = get_user_playlists(token_info)
    tracks_data = []
    
    for playlist in playlists:
        playlist_id = playlist['id']
        tracks = get_playlist_tracks(token_info, playlist_id)
        
        for track in tracks:
            track_info = track['track']
            tracks_data.append({
                'track_name': track_info['name'],
                'artist': track_info['artists'][0]['name'],
                'album': track_info['album']['name'],
                'genre': track_info['album'].get('genres', ['Sconosciuto'])[0]
            })
    
    return pd.DataFrame(tracks_data)