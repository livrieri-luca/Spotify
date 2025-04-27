from flask import Blueprint, request, render_template, session, redirect, url_for
from services.analyse import analizza_playlist  # Funzione che si occupa di analizzare una playlist
import spotipy  # Libreria per interagire con le API di Spotify
from services.spotify_api import get_spotify_object, sp_public  # Funzioni per gestire l'autenticazione con Spotify

# Creiamo un Blueprint per gestire le rotte legate all'analisi delle playlist
analizza_bp = Blueprint('analizza', __name__)

# Questa rotta prende l'ID della playlist e mostra l'analisi corrispondente
@analizza_bp.route('/analizza/<playlist_id>')
def analizza_playlist_view(playlist_id):
    # Controlliamo se c'è un token valido nella sessione dell'utente
    token_info = session.get('token_info', None)
    
    # Se c'è un token, usiamo un oggetto Spotify autenticato, altrimenti usiamo una versione pubblica
    sp = get_spotify_object(token_info) if token_info else sp_public

    # Recuperiamo le informazioni della playlist tramite il suo ID
    playlist = sp.playlist(playlist_id)
    tracks = playlist['tracks']['items']  # Otteniamo la lista dei brani presenti nella playlist
    playlist_name = playlist['name']  # Prendiamo il nome della playlist

    # Passiamo i brani alla funzione di analisi per ottenere i grafici o i risultati
    plots = analizza_playlist(tracks)

    # Renderizziamo la pagina 'analisi.html' con il nome della playlist, i brani e i grafici
    return render_template('analisi.html', playlist_name=playlist_name, tracks=tracks, plots=plots)
