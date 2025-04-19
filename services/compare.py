import io
import base64
import matplotlib.pyplot as plt
from collections import Counter
import pandas as pd
from spotipy import Spotify
from services.spotify_api import sp_public  # deve restituire un access token valido

def plot_to_base64():
    """
    Funzione per generare l'immagine del grafico e restituirla come stringa Base64.
    """
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()
    return img_base64

def confronta_playlist(playlist_id1, playlist_id2):
    sp = sp_public

    def get_playlist_tracks(playlist_id):
        """
        Funzione per ottenere tutti i brani di una playlist.
        """
        try:
            results = sp.playlist_items(playlist_id, additional_types=["track"])
            tracks = results['items']
            while results['next']:
                results = sp.next(results)
                tracks.extend(results['items'])
            return [t['track'] for t in tracks if t['track']]
        except Exception as e:
            print(f"Errore nel recupero dei brani per la playlist {playlist_id}: {e}")
            return []

    def estrai_artisti_e_generi(tracks):
        """
        Funzione per estrarre artisti e generi da una lista di tracce.
        """
        artisti = [artista['name'] for track in tracks for artista in track['artists']]
        generi = []
        for artista in set(artisti):
            res = sp.search(q=f'artist:{artista}', type='artist', limit=1)
            items = res.get('artists', {}).get('items', [])
            if items:
                generi.extend(items[0].get('genres', []))
        return artisti, generi

    # Ottenere le tracce dalle playlist
    tracks1 = get_playlist_tracks(playlist_id1)
    tracks2 = get_playlist_tracks(playlist_id2)

    if not tracks1 or not tracks2:
        return {"error": "Errore nel recupero delle tracce delle playlist."}

    # Titoli delle tracce
    titoli1 = set((t['name'], t['artists'][0]['name']) for t in tracks1)
    titoli2 = set((t['name'], t['artists'][0]['name']) for t in tracks2)

    # Brani comuni
    comuni = list(titoli1 & titoli2)
    somiglianza = round(len(comuni) / min(len(titoli1), len(titoli2)) * 100, 2) if min(len(titoli1), len(titoli2)) > 0 else 0

    # Artisti e generi
    artisti1, generi1 = estrai_artisti_e_generi(tracks1)
    artisti2, generi2 = estrai_artisti_e_generi(tracks2)

    artisti_comuni = sorted(set(artisti1) & set(artisti2))
    freq1 = Counter([a for a in artisti1 if a in artisti_comuni])
    freq2 = Counter([a for a in artisti2 if a in artisti_comuni])

    df_artisti = pd.DataFrame({
        'Artista': artisti_comuni,
        'Frequenza Playlist 1': [freq1[a] for a in artisti_comuni],
        'Frequenza Playlist 2': [freq2[a] for a in artisti_comuni]
    })

    # Grafico frequenza artisti in comune
    plt.figure(figsize=(10, 6))
    x = df_artisti['Artista']
    width = 0.35
    plt.bar(x, df_artisti['Frequenza Playlist 1'], width=width, label='Playlist 1', align='center')
    plt.bar(x, df_artisti['Frequenza Playlist 2'], width=width, label='Playlist 2', align='edge')
    plt.xticks(rotation=45, ha='right')
    plt.legend()
    plt.title("Frequenza degli Artisti in Comune")
    plt.tight_layout()
    img_artisti = plot_to_base64()

    # Grafico popolarità media
    pop1 = [t['popularity'] for t in tracks1 if t.get('popularity') is not None]
    pop2 = [t['popularity'] for t in tracks2 if t.get('popularity') is not None]

    plt.figure(figsize=(6, 4))
    plt.bar(['Playlist 1', 'Playlist 2'], [sum(pop1)/len(pop1), sum(pop2)/len(pop2)], color=['skyblue', 'orange'])
    plt.ylabel('Popolarità media')
    plt.title("Confronto della Popolarità Media")
    img_popolarita = plot_to_base64()

    # Generi musicali
    top_generi = list((Counter(generi1) + Counter(generi2)).most_common(10))
    generi_top = [g for g, _ in top_generi]

    df_generi = pd.DataFrame({
        'Genere': generi_top,
        'Playlist 1': [generi1.count(g) for g in generi_top],
        'Playlist 2': [generi2.count(g) for g in generi_top]
    })

    df_generi.set_index('Genere').plot(kind='bar', figsize=(10, 6))
    plt.title("Top 10 Generi Musicali")
    plt.ylabel("Frequenza")
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    img_generi = plot_to_base64()

    # Recupera il nome delle playlist
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
