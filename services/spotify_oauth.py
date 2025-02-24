import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials

# Configurazione credenziali Spotify
SPOTIFY_CLIENT_ID = "b6c825a1f5364751a178db12c7373bd8"
SPOTIFY_CLIENT_SECRET = "329a625d0f1e4a9c8a5b43918a91ae0d"
SPOTIFY_REDIRECT_URI = "https://5000-livrieriluca-spotify-gab9a45hcsp.ws-eu118.gitpod.io/callback"
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
    return sp_public  # Accesso pubblico senza login
