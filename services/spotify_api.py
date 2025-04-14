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
    # Verifica se il token è valido e ha lo scope 'user-top-read'
    if token_info:
        scopes = token_info.get('scope', '')
        if 'user-top-read' not in scopes:
            print("Lo scope 'user-top-read' non è presente. Richiedi il permesso all'utente.")
            return None  # Ritorna None se lo scope non è presente
        return spotipy.Spotify(auth=token_info['access_token'])  # Restituisci Spotify object se lo scope è corretto
    else:
        print("Token non presente.")
        return sp_public  # Restituisce l'oggetto pubblico se non è presente un token valido4
# Funzione per recuperare i brani pubblici tramite Spotify API
def get_public_tracks():
    # Recupera i brani più popolari pubblici (modifica la query se necessario)
    tracks = sp.current_user_top_tracks(limit=10)

def get_user_info(token_info):
    sp = get_spotify_object(token_info)
    if sp:
        return sp.current_user()  # Ottieni le informazioni dell'utente
    return None
  
def get_user_playlists(token_info):
    sp = get_spotify_object(token_info)
    if sp:
        return sp.current_user_playlists()['items']  # Ottieni le playlist dell'utente
    return []

def get_playlist_tracks(token_info, playlist_id):
    try:
        sp = get_spotify_object(token_info)
        if sp:
            # Recupera le tracce della playlist
            results = sp.playlist_tracks(playlist_id)
            tracks = results['items']  # Otteniamo la lista dei brani
            while results['next']:  # Controlliamo se ci sono altre pagine di brani
                results = sp.next(results)
                tracks.extend(results['items'])
            return tracks
    except Exception as e:
        print(f"Errore nel recupero dei brani della playlist {playlist_id}: {e}")
    return []  # Se c'è un errore, ritorna una lista vuota

def get_track_details(token_info, track_id):
    sp = get_spotify_object(token_info)
    if sp:
        track = sp.track(track_id)
        artist_details = sp.artist(track['artists'][0]['id'])

        genres = artist_details.get('genres', [])
        genre = genres[0] if genres else 'Genere sconosciuto'
        
        return track, genre
    return None, 'Genere sconosciuto'

def get_all_tracks(token_info, playlist_id=None):
    sp = get_spotify_object(token_info)
    if sp:
        tracks_data = []

        if playlist_id: 
            tracks = get_playlist_tracks(token_info, playlist_id)
        else:
         
            playlists = get_user_playlists(token_info)

            for playlist in playlists:
                playlist_id = playlist['id']
                tracks = get_playlist_tracks(token_info, playlist_id)


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
    return pd.DataFrame([])  


def force_reauthentication():
    auth_url = sp_oauth.get_authorize_url()
    print(f"Apri questo link nel tuo browser per autenticarti: {auth_url}")
    response = input("Incolla qui l'URL di ritorno dopo l'autenticazione: ")
    token_info = sp_oauth.get_access_token(response)
    return token_info

