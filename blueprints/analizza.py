from flask import Blueprint, request, render_template, session, redirect, url_for, flash
from services.analyse import analizza_playlist
import spotipy
from services.spotify_api import get_spotify_object, sp_public

# Creiamo un Blueprint per gestire le rotte legate all'analisi delle playlist
analizza_bp = Blueprint('analizza', __name__)

# Questa rotta prende l'ID della playlist e mostra l'analisi corrispondente
@analizza_bp.route('/analizza/<playlist_id>')
def analizza_playlist_view(playlist_id):
    # Controlliamo se c'è un token valido nella sessione dell'utente
    token_info = session.get('token_info', None)
    
    # Se non c'è un token valido, reindirizziamo alla pagina di login
    if not token_info:
        flash('Devi effettuare il login per analizzare le playlist.', 'danger')
        return redirect(url_for('auth.login'))  # Aggiungi la rotta di login

    # Se c'è un token, usiamo un oggetto Spotify autenticato
    sp = get_spotify_object(token_info) if token_info else sp_public
    
    try:
        # Recuperiamo le informazioni della playlist tramite il suo ID
        playlist = sp.playlist(playlist_id)
    except spotipy.exceptions.SpotifyException:
        # Gestiamo errori in caso di problemi con Spotify, come playlist non trovate
        flash('Si è verificato un errore nel recupero della playlist. Verifica l\'ID.', 'danger')
        return redirect(url_for('home'))  # Reindirizza a una pagina principale o home

    tracks = playlist['tracks']['items']  # Otteniamo la lista dei brani presenti nella playlist
    playlist_name = playlist['name']  # Prendiamo il nome della playlist

    # Passiamo i brani alla funzione di analisi per ottenere i grafici o i risultati
    try:
        plots = analizza_playlist(tracks)
    except Exception as e:
        # Gestiamo eventuali errori nell'analisi della playlist
        flash(f'Errore nell\'analisi della playlist: {str(e)}', 'danger')
        return redirect(url_for('home'))  # Reindirizza alla home in caso di errore nell'analisi

    # Renderizziamo la pagina 'analisi.html' con il nome della playlist, i brani e i grafici
    return render_template('analisi.html', playlist_name=playlist_name, tracks=tracks, plots=plots)

