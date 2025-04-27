# Importazione dei moduli necessari da Flask
from flask import Blueprint, request, render_template
# Importazione della funzione personalizzata per confrontare due playlist
from services.compare import confronta_playlist

# Creiamo un Blueprint per gestire le rotte legate al confronto delle playlist
compara_bp = Blueprint('compara', __name__)

# Definiamo la rotta che permette di confrontare due playlist
@compara_bp.route('/compara')
def compara_view():
    # Recuperiamo gli ID delle due playlist dai parametri della query string (?p1=...&p2=...)
    playlist1 = request.args.get('p1')
    playlist2 = request.args.get('p2')

    # Se uno dei due ID non viene fornito, restituiamo un errore (400 Bad Request)
    if not playlist1 or not playlist2:
        return "Playlist mancanti", 400

    # Chiamiamo la funzione che esegue il confronto tra le due playlist e otteniamo i dati da mostrare
    dati = confronta_playlist(playlist1, playlist2)

    # Renderizziamo la pagina 'compara.html' passando i dati ottenuti dalla funzione
    return render_template('compara.html', **dati)
