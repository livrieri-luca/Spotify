import io
import base64
import matplotlib.pyplot as plt
from collections import Counter
import pandas as pd
from spotipy import Spotify
from services.spotify_api import sp_public 

def plot_to_base64():
    """
    Funzione per generare il grafico e restituirlo come una stringa in formato Base64.
    Questo è utile per visualizzare il grafico in una pagina web senza doverlo salvare come file.
    """
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')  # Salva il grafico in un buffer
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')  # Codifica il buffer in Base64
    plt.close()  # Chiude la figura per evitare che venga mantenuta in memoria
    return img_base64

def confronta_playlist(playlist_id1, playlist_id2):
    sp = sp_public

    def get_playlist_tracks(playlist_id):
        """
        Funzione per ottenere tutte le tracce di una playlist specificata dal suo ID.
        Utilizza l'API di Spotify per ottenere i brani e gestire la paginazione.
        """
        try:
            results = sp.playlist_items(playlist_id, additional_types=["track"])
            tracks = results['items']
            while results['next']:
                results = sp.next(results)
                tracks.extend(results['items'])  # Aggiunge nuove tracce alla lista
            return [t['track'] for t in tracks if t['track']]  # Filtra solo le tracce valide
        except Exception as e:
            print(f"Errore nel recupero dei brani per la playlist {playlist_id}: {e}")
            return []  # Restituisce una lista vuota in caso di errore

    def estrai_artisti_e_generi(tracks):
        """
        Estrae gli artisti e i generi musicali da una lista di tracce.
        Utilizza l'API di Spotify per cercare informazioni sugli artisti.
        """
        artisti = [artista['name'] for track in tracks for artista in track['artists']]  # Estrae gli artisti
        generi = []
        for artista in set(artisti):  # Evita duplicati tra gli artisti
            res = sp.search(q=f'artist:{artista}', type='artist', limit=1)
            items = res.get('artists', {}).get('items', [])
            if items:
                generi.extend(items[0].get('genres', []))  # Aggiunge i generi dell'artista
        return artisti, generi

    # Otteniamo le tracce per entrambe le playlist
    tracks1 = get_playlist_tracks(playlist_id1)
    tracks2 = get_playlist_tracks(playlist_id2)

    if not tracks1 or not tracks2:  # Se una delle playlist non ha tracce valide, restituiamo un errore
        return {"error": "Errore nel recupero delle tracce delle playlist."}

    # Estrazione dei titoli delle tracce e degli artisti
    titoli1 = set((t['name'], t['artists'][0]['name']) for t in tracks1)
    titoli2 = set((t['name'], t['artists'][0]['name']) for t in tracks2)

    # Troviamo i brani comuni tra le due playlist
    comuni = list(titoli1 & titoli2)
    somiglianza = round(len(comuni) / min(len(titoli1), len(titoli2)) * 100, 2) if min(len(titoli1), len(titoli2)) > 0 else 0

    # Estrazione degli artisti e dei generi musicali per ciascuna playlist
    artisti1, generi1 = estrai_artisti_e_generi(tracks1)
    artisti2, generi2 = estrai_artisti_e_generi(tracks2)

    # Artisti comuni nelle due playlist
    artisti_comuni = sorted(set(artisti1) & set(artisti2))
    freq1 = Counter([a for a in artisti1 if a in artisti_comuni])  # Conta le occorrenze degli artisti nella prima playlist
    freq2 = Counter([a for a in artisti2 if a in artisti_comuni])  # Conta le occorrenze degli artisti nella seconda playlist

    # Creiamo un DataFrame per visualizzare la frequenza degli artisti comuni
    df_artisti = pd.DataFrame({
        'Artista': artisti_comuni,
        'Frequenza Playlist 1': [freq1[a] for a in artisti_comuni],
        'Frequenza Playlist 2': [freq2[a] for a in artisti_comuni]
    })

    # Creiamo un grafico a barre per mostrare la frequenza degli artisti in comune tra le playlist
    plt.figure(figsize=(10, 6))
    x = df_artisti['Artista']
    width = 0.35
    plt.bar(x, df_artisti['Frequenza Playlist 1'], width=width, label='Playlist 1', align='center')
    plt.bar(x, df_artisti['Frequenza Playlist 2'], width=width, label='Playlist 2', align='edge')
    plt.xticks(rotation=45, ha='right')
    plt.legend()
    plt.title("Frequenza degli Artisti in Comune")
    plt.tight_layout()
    img_artisti = plot_to_base64()  # Converte il grafico in formato Base64

    # Confrontiamo la popolarità media delle due playlist
    pop1 = [t['popularity'] for t in tracks1 if t.get('popularity') is not None]
    pop2 = [t['popularity'] for t in tracks2 if t.get('popularity') is not None]

    # Creiamo un grafico a barre per confrontare la popolarità media delle due playlist
    plt.figure(figsize=(6, 4))
    plt.bar(['Playlist 1', 'Playlist 2'], [sum(pop1)/len(pop1), sum(pop2)/len(pop2)], color=['skyblue', 'orange'])
    plt.ylabel('Popolarità media')
    plt.title("Confronto della Popolarità Media")
    img_popolarita = plot_to_base64()  # Converte il grafico in formato Base64

    # Identifichiamo i generi musicali più presenti nelle due playlist
    top_generi = list((Counter(generi1) + Counter(generi2)).most_common(10))
    generi_top = [g for g, _ in top_generi]

    # Creiamo un DataFrame per visualizzare la frequenza dei generi musicali
    df_generi = pd.DataFrame({
        'Genere': generi_top,
        'Playlist 1': [generi1.count(g) for g in generi_top],
        'Playlist 2': [generi2.count(g) for g in generi_top]
    })

    df_generi.set_index('Genere').plot(kind='bar', figsize=(10, 6))  # Creiamo un grafico a barre per i generi
    plt.title("Top 10 Generi Musicali")
    plt.ylabel("Frequenza")
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    img_generi = plot_to_base64()  # Converte il grafico in formato Base64

    # Recuperiamo il nome delle playlist da Spotify
    nome1 = sp.playlist(playlist_id1).get('name', 'Playlist 1')
    nome2 = sp.playlist(playlist_id2).get('name', 'Playlist 2')

    return {
        'common_tracks': [f"{t[0]} - {t[1]}" for t in comuni],
        'similarity_percentage': somiglianza,
        'img_artisti': img_artisti,
        'img_popolarita': img_popolarita,
        'img_generi': img_generi,
        'artisti_comuni': list(artisti_comuni),
        'playlist_name1': nome1,
        'playlist_name2': nome2
    }
