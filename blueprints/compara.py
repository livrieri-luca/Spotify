from flask import Blueprint, request, render_template, flash, redirect, url_for
from services.compare import confronta_playlist
import spotipy

# Creiamo un Blueprint per gestire le rotte legate al confronto delle playlist
compara_bp = Blueprint('compara', __name__)

# Rotta per il confronto tra due playlist
@compara_bp.route('/compara', methods=['GET', 'POST'])
def compara_view():
    # Variabili per raccogliere gli ID delle playlist
    playlist1 = request.args.get('p1')
    playlist2 = request.args.get('p2')

    # Controllo che gli ID siano presenti, se no, chiediamo di inserirli
    if not playlist1 or not playlist2:
        flash("Per favore, inserisci gli ID di due playlist da confrontare.", "error")
        return render_template('compara.html', p1=playlist1, p2=playlist2)

    # Tentiamo di eseguire il confronto
    try:
        # Chiamiamo la funzione che esegue il confronto tra le due playlist
        dati = confronta_playlist(playlist1, playlist2)
        # Se il confronto ha successo, renderizziamo la pagina con i dati
        return render_template('compara.html', **dati)
    except Exception as e:
        # Se qualcosa va storto (ad esempio ID playlist non validi), mostriamo un errore
        flash(f"Errore nel confronto delle playlist: {str(e)}", "error")
        return redirect(url_for('compara.compara_view'))

# Funzione per gestire la ricerca delle playlist (opzionale)
@compara_bp.route('/search', methods=['GET'])
def search_playlists():
    # Recuperiamo l'input di ricerca dall'utente (può essere una parte del nome della playlist)
    query = request.args.get('query', '')
    if query:
        try:
            # Eseguiamo una ricerca su Spotify
            sp = spotipy.Spotify(auth=session.get('token_info')['access_token'])
            results = sp.search(q=query, type='playlist', limit=10)
            playlists = results['playlists']['items']
        except Exception as e:
            flash(f"Errore durante la ricerca: {str(e)}", "error")
            playlists = []
    else:
        playlists = []

    return render_template('search_playlists.html', playlists=playlists, query=query)

