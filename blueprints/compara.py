# Importazione dei moduli necessari da Flask
from flask import Blueprint, request, render_template
# Importazione della funzione personalizzata che confronta due playlist
from services.compare import confronta_playlist

# Creazione di un Blueprint per raggruppare le rotte relative al confronto
compara_bp = Blueprint('compara', __name__)

# Definizione della rotta per il confronto tra due playlist
@compara_bp.route('/compara')
def compara_view():
    # Otteniamo gli ID delle due playlist dai parametri della query string (?p1=...&p2=...)
    playlist1 = request.args.get('p1')
    playlist2 = request.args.get('p2')

    # Se uno dei due ID non è stato fornito, restituiamo un errore 400 (Bad Request)
    if not playlist1 or not playlist2:
        return "Playlist mancanti", 400

    # Chiamata alla funzione di confronto che restituisce un dizionario di dati da visualizzare
    dati = confronta_playlist(playlist1, playlist2)

    # Renderizza la pagina HTML 'compara.html', passando i dati ottenuti dalla funzione
    return render_template('compara.html', **dati)
