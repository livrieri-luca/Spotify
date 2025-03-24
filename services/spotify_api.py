import spotipy 
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
import pandas as pd

SPOTIFY_CLIENT_ID = "033d14b0d2cd48068699ee4bad749e9b"
SPOTIFY_CLIENT_SECRET = "e4ce5171826d4cbe8a7d30c84dec6c5d"
SPOTIFY_REDIRECT_URI = "https://5000-livrieriluca-spotify-rp9y5agng9e.ws-eu118.gitpod.io/callback"
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
    genre = artist_details.get('genres', ['Genere sconosciuto'])[0]
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
