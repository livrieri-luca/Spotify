import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
import pandas as pd

# Configurazione delle credenziali per accedere a Spotify API
SPOTIFY_CLIENT_ID = "200875a1e6d941bebe8d3ab86bd8dadf"
SPOTIFY_CLIENT_SECRET = "c35e9f794b0e44baaf935f5e8638b320"
SPOTIFY_REDIRECT_URI = "https://5000-livrieriluca-spotify-g8zmem5u6r6.ws-eu118.gitpod.io/callback"
SPOTIFY_SCOPE = "user-read-private user-read-email playlist-read-private user-top-read"

# Creazione dell'oggetto di autenticazione per ottenere i token di accesso
sp_oauth = SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope=SPOTIFY_SCOPE,
    show_dialog=True
)

# Creazione dell'oggetto Spotify per l'accesso pubblico senza autenticazione dell'utente
sp_public = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET
))

def get_spotify_object(token_info=None):
    """
    Restituisce un oggetto Spotify autenticato. Se 'token_info' è fornito,
    usa il token di accesso dell'utente, altrimenti usa l'accesso pubblico (client credentials).
    """
    if token_info:
        scopes = token_info.get('scope', '')
        if 'user-top-read' not in scopes:  # Verifica se lo scope richiesto è presente
            print("Lo scope 'user-top-read' non è presente.")
            return None
        return spotipy.Spotify(auth=token_info['access_token'])  # Restituisce oggetto autenticato
    else:
        print("Token non presente. Uso client pubblico.")
        return sp_public  # Restituisce l'oggetto per accesso pubblico

def get_public_tracks(token_info=None):
    """
    Ottiene i top 10 brani dell'utente autenticato (se il token è fornito).
    Se il token non è presente, restituisce un elenco vuoto.
    """
    sp = get_spotify_object(token_info)
    if sp:
        try:
            return sp.current_user_top_tracks(limit=10)  # Ottieni le 10 tracce principali dell'utente
        except Exception as e:
            print(f"Errore nel recupero dei top tracks: {e}")
    return []  # Restituisce lista vuota in caso di errore

def get_user_info(token_info):
    """
    Ottiene le informazioni dell'utente autenticato, come nome e email.
    """
    sp = get_spotify_object(token_info)
    if sp:
        return sp.current_user()  # Restituisce informazioni dell'utente
    return None  # Restituisce None in caso di errore

def get_user_playlists(token_info):
    """
    Ottiene tutte le playlist dell'utente autenticato.
    """
    sp = get_spotify_object(token_info)
    if sp:
        return sp.current_user_playlists()['items']  # Restituisce la lista di playlist dell'utente
    return []  # Restituisce lista vuota in caso di errore

def get_playlist_tracks(token_info, playlist_id):
    """
    Ottiene tutte le tracce di una playlist specificata dall'ID.
    Gestisce la paginazione per recuperare tutte le tracce.
    """
    try:
        sp = get_spotify_object(token_info)
        if sp:
            results = sp.playlist_tracks(playlist_id)
            tracks = results['items']
            while results['next']:  # Gestisce la paginazione
                results = sp.next(results)
                tracks.extend(results['items'])
            return tracks  # Restituisce tutte le tracce della playlist
    except Exception as e:
        print(f"Errore nel recupero dei brani della playlist {playlist_id}: {e}")
    return []  # Restituisce lista vuota in caso di errore

def get_track_details(sp, track_id):
    """
    Ottiene i dettagli di una traccia, inclusi il genere musicale dell'artista.
    """
    try:
        track = sp.track(track_id)  # Ottieni informazioni sulla traccia
        artist_id = track['artists'][0]['id']  # ID dell'artista
        artist = sp.artist(artist_id)  # Ottieni informazioni sull'artista
        genres = artist.get('genres', [])  # Recupera i generi dell'artista
        genre = genres[0] if genres else 'Genere sconosciuto'  # Se non ci sono generi, restituisce 'Genere sconosciuto'
        return track, genre  # Restituisce dettagli traccia e genere
    except Exception as e:
        print(f"Errore nel recupero dettagli della traccia {track_id}: {e}")
        return None, 'Genere sconosciuto'  # Restituisce valori predefiniti in caso di errore

def get_all_tracks(token_info, playlist_id=None):
    """
    Ottiene tutte le tracce da una playlist (se fornito un playlist_id),
    o tutte le tracce da tutte le playlist dell'utente (se playlist_id è None).
    Restituisce i dati delle tracce come un DataFrame di Pandas.
    """
    sp = get_spotify_object(token_info)
    if not sp:
        return pd.DataFrame([])  # Restituisce un DataFrame vuoto se non c'è un oggetto Spotify valido

    tracks_data = []  # Lista per raccogliere i dati delle tracce

    if playlist_id:
        tracks = get_playlist_tracks(token_info, playlist_id)  # Ottieni tracce dalla playlist specifica
    else:
        playlists = get_user_playlists(token_info)  # Ottieni tutte le playlist dell'utente
        tracks = []
        for playlist in playlists:
            pid = playlist['id']  # Ottieni ID playlist
            tracks += get_playlist_tracks(token_info, pid)  # Aggiungi tracce alla lista

    for track_wrapper in tracks:
        track_info = track_wrapper['track']
        if not track_info:  # Ignora tracce null o incomplete
            continue
        release_date = track_info['album'].get('release_date', 'Unknown')  # Ottieni data di rilascio
        popularity = track_info.get('popularity', 0)  # Ottieni popolarità della traccia
        duration_ms = track_info.get('duration_ms', 0)  # Ottieni durata della traccia

        _, genre = get_track_details(token_info, track_info['id'])  # Ottieni dettagli traccia e genere

        tracks_data.append({
            'track_name': track_info['name'],
            'artist': track_info['artists'][0]['name'],
            'album': track_info['album']['name'],
            'genre': genre,
            'release_date': release_date,
            'duration_ms': duration_ms,
            'popularity': popularity
        })

    return pd.DataFrame(tracks_data)  # Restituisce i dati delle tracce come DataFrame di Pandas

def force_reauthentication():
    """
    Forza una nuova autenticazione dell'utente tramite il flusso OAuth di Spotify.
    Restituisce il token di accesso dopo che l'utente ha completato l'autenticazione.
    """
    auth_url = sp_oauth.get_authorize_url()  # Ottieni l'URL per l'autenticazione
    print(f"Apri questo link nel tuo browser per autenticarti: {auth_url}")
    response = input("Incolla qui l'URL di ritorno dopo l'autenticazione: ")  # Chiede all'utente di incollare l'URL di ritorno
    token_info = sp_oauth.get_access_token(response)  # Ottieni il token di accesso
    return token_info  # Restituisce il token di accesso ottenuto
