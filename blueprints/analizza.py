from flask import Blueprint, request, render_template, session, redirect, url_for
from services.analyse import analizza_playlist  # Funzione personalizzata per analizzare una playlist
import spotipy  # Libreria ufficiale per interagire con le API di Spotify
from services.spotify_api import get_spotify_object, sp_public  # Funzioni per gestire l'autenticazione con Spotify

# Creiamo un Blueprint per raggruppare le rotte relative all'analisi della playlist
analizza_bp = Blueprint('analizza', __name__)

# Definiamo una rotta che riceve un ID di playlist e mostra l'analisi
@analizza_bp.route('/analizza/<playlist_id>')
def analizza_playlist_view(playlist_id):
    # Recupera le informazioni del token dalla sessione, se l'utente è autenticato
    token_info = session.get('token_info', None)
    
    # Otteniamo un oggetto Spotify autenticato o pubblico in base alla disponibilità del token
    sp = get_spotify_object(token_info) if token_info else sp_public

    # Recuperiamo i dati della playlist specificata tramite l'ID
    playlist = sp.playlist(playlist_id)
    tracks = playlist['tracks']['items']  # Lista dei brani presenti nella playlist
    playlist_name = playlist['name']  # Nome della playlist

    # Passiamo i brani al servizio di analisi per generare i grafici o i risultati
    plots = analizza_playlist(tracks)

    # Renderizziamo la pagina HTML 'brani.html', passando nome playlist, tracce e grafici/analisi
    return render_template('analisi.html', playlist_name=playlist_name, tracks=tracks, plots=plots)