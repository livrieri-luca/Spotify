import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
import pandas as pd

SPOTIFY_CLIENT_ID = "200875a1e6d941bebe8d3ab86bd8dadf"
SPOTIFY_CLIENT_SECRET = "c35e9f794b0e44baaf935f5e8638b320"
SPOTIFY_REDIRECT_URI = "https://5000-livrieriluca-spotify-5yvduxdkgtx.ws-eu118.gitpod.io/callback"
SPOTIFY_SCOPE = "user-read-private user-read-email playlist-read-private user-top-read"

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
    if token_info:
        scopes = token_info.get('scope', '')
        if 'user-top-read' not in scopes:
            print("Lo scope 'user-top-read' non è presente.")
            return None
        return spotipy.Spotify(auth=token_info['access_token'])
    else:
        print("Token non presente. Uso client pubblico.")
        return sp_public

def get_public_tracks(token_info=None):
    sp = get_spotify_object(token_info)
    if sp:
        try:
            return sp.current_user_top_tracks(limit=10)
        except Exception as e:
            print(f"Errore nel recupero dei top tracks: {e}")
    return []

def get_user_info(token_info):
    sp = get_spotify_object(token_info)
    if sp:
        return sp.current_user()
    return None

def get_user_playlists(token_info):
    sp = get_spotify_object(token_info)
    if sp:
        return sp.current_user_playlists()['items']
    return []

def get_playlist_tracks(token_info, playlist_id):
    try:
        sp = get_spotify_object(token_info)
        if sp:
            results = sp.playlist_tracks(playlist_id)
            tracks = results['items']
            while results['next']:
                results = sp.next(results)
                tracks.extend(results['items'])
            return tracks
    except Exception as e:
        print(f"Errore nel recupero dei brani della playlist {playlist_id}: {e}")
    return []
def get_track_details(sp, track_id):
    try:
        track = sp.track(track_id)
        artist_id = track['artists'][0]['id']
        artist = sp.artist(artist_id)
        genres = artist.get('genres', [])
        genre = genres[0] if genres else 'Genere sconosciuto'
        return track, genre
    except Exception as e:
        print(f"Errore nel recupero dettagli della traccia {track_id}: {e}")
        return None, 'Genere sconosciuto'


def get_all_tracks(token_info, playlist_id=None):
    sp = get_spotify_object(token_info)
    if not sp:
        return pd.DataFrame([])

    tracks_data = []

    if playlist_id:
        tracks = get_playlist_tracks(token_info, playlist_id)
    else:
        playlists = get_user_playlists(token_info)
        tracks = []
        for playlist in playlists:
            pid = playlist['id']
            tracks += get_playlist_tracks(token_info, pid)

    for track_wrapper in tracks:
        track_info = track_wrapper['track']
        if not track_info:  # A volte ci sono tracce null
            continue
        release_date = track_info['album'].get('release_date', 'Unknown')
        popularity = track_info.get('popularity', 0)
        duration_ms = track_info.get('duration_ms', 0)

        _, genre = get_track_details(token_info, track_info['id'])

        tracks_data.append({
            'track_name': track_info['name'],
            'artist': track_info['artists'][0]['name'],
            'album': track_info['album']['name'],
            'genre': genre,
            'release_date': release_date,
            'duration_ms': duration_ms,
            'popularity': popularity
        })

    return pd.DataFrame(tracks_data)

def force_reauthentication():
    auth_url = sp_oauth.get_authorize_url()
    print(f"Apri questo link nel tuo browser per autenticarti: {auth_url}")
    response = input("Incolla qui l'URL di ritorno dopo l'autenticazione: ")
    token_info = sp_oauth.get_access_token(response)
    return token_info
