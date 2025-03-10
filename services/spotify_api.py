import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials

# Configurazione credenziali Spotify
SPOTIFY_CLIENT_ID = "200875a1e6d941bebe8d3ab86bd8dadf"
SPOTIFY_CLIENT_SECRET = "c35e9f794b0e44baaf935f5e8638b320"
SPOTIFY_REDIRECT_URI = "https://5000-livrieriluca-spotify-88u1ji5dncl.ws-eu118.gitpod.io/callback"
SPOTIFY_SCOPE = "user-read-private user-read-email playlist-read-private"

# Autenticazione con OAuth per utenti loggati
sp_oauth = SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope=SPOTIFY_SCOPE,
    show_dialog=True
)

# Autenticazione pubblica per chi non ha fatto login
sp_public = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET
))

# Funzione per ottenere l'oggetto Spotify corretto
def get_spotify_object(token_info=None):
    if token_info:
        return spotipy.Spotify(auth=token_info['access_token'])
    return sp_public  # Accesso limitato per utenti non autenticati

# Funzione per ottenere l'informazione dell'utente attualmente autenticato
def get_user_info(token_info):
    sp = get_spotify_object(token_info)
    return sp.current_user()

# Funzione per ottenere le playlist dell'utente
def get_user_playlists(token_info):
    sp = get_spotify_object(token_info)
    return sp.current_user_playlists()['items']

# Funzione per ottenere i brani di una playlist
def get_playlist_tracks(token_info, playlist_id):
    sp = get_spotify_object(token_info)
    return sp.playlist_tracks(playlist_id)['items']

# Funzione per ottenere i dettagli di un brano
def get_track_details(token_info, track_id):
    sp = get_spotify_object(token_info)
    track = sp.track(track_id)
    artist_id = track['artists'][0]['id']
    artist_details = sp.artist(artist_id)
    genre = artist_details.get('genres', [])
    genre = genre[0] if genre else 'Genere sconosciuto'
    return track, genre
