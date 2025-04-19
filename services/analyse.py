import pandas as pd
import matplotlib.pyplot as plt
import io
import base64

def plot_to_base64(fig):
    """Converte un grafico Matplotlib in una stringa Base64 per l'HTML."""
    img = io.BytesIO()
    fig.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    return base64.b64encode(img.getvalue()).decode()

def analizza_playlist(tracks):
    """Analizza i brani della playlist e genera statistiche e grafici."""
    if not tracks:
        return {}

    data = []
    for track in tracks:
        track_info = track.get('track', None)
        if not track_info:
            continue
        artists = [artist['name'] for artist in track_info.get('artists', []) if artist.get('name')]
        album = track_info.get('album', {}).get('name', 'Sconosciuto')
        genres = [genre for genre in track_info.get('album', {}).get('genres', []) if genre]
        data.append({
            'title': track_info.get('name', 'Sconosciuto'), 
            'artist': ', '.join(artists) if artists else 'Sconosciuto',
            'album': album, 
            'genres': ', '.join(genres) if genres else 'Sconosciuto'
        })

    df = pd.DataFrame(data)

    plots = {}

    # Top 5 Artisti più presenti
    artist_list = []
    for track in tracks:
        track_info = track.get('track', None)
        if not track_info:
            continue
        artists = track_info.get('artists', [])
        for artist in artists:
            artist_list.append(artist['name'])

    artist_series = pd.Series(artist_list)
    artist_count = artist_series.value_counts().head(5)

    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.barh(artist_count.index, artist_count.values, color='purple')
    ax.set_title('Top 5 Artisti più Presenti')
    ax.set_xlabel('Numero di Brani')
    ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
    ax.bar_label(bars, labels=[str(v) for v in artist_count.values], padding=3)
    plots['top_artists'] = plot_to_base64(fig)

    # Top 5 Album più presenti
    album_count = df['album'].value_counts().head(5)
    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.barh(album_count.index, album_count.values, color='orange')
    ax.set_title('Top 5 Album più Presenti')
    ax.set_xlabel('Numero di Brani')
    ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
    ax.bar_label(bars, labels=[str(v) for v in album_count.values], padding=3)
    plots['top_albums'] = plot_to_base64(fig)

    # Distribuzione Generi Musicali
    if not df['genres'].isna().all():
        genre_list = df['genres'].str.split(', ').explode().dropna()
        genre_count = genre_list.value_counts().head(7)
        fig, ax = plt.subplots(figsize=(6, 4))
        bars = ax.barh(genre_count.index, genre_count.values, color='red')
        ax.set_title('Distribuzione Generi Musicali')
        ax.set_xlabel('Numero di Brani')
        ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
        ax.bar_label(bars, labels=[str(v) for v in genre_count.values], padding=3)
        plots['top_genres'] = plot_to_base64(fig)

    # Distribuzione della Durata dei Brani
    duration_data = []
    for track in tracks:
        track_info = track.get('track', {})
        duration_ms = track_info.get('duration_ms')
        if duration_ms:
            duration_min = duration_ms / 60000
            duration_data.append(duration_min)

    if duration_data:
        fig, ax = plt.subplots(figsize=(6, 4))
        
        # Istogramma e raccolta delle altezze delle barre
        counts, bins, patches = ax.hist(duration_data, bins=15, color='goldenrod', edgecolor='black')
        ax.set_title('Variazione della Durata dei Brani nella Playlist')
        ax.set_xlabel('Durata (minuti)')
        ax.set_ylabel('Frequenza')
        # Imposta i tick dell’asse Y solo sui valori interi presenti come altezza delle barre
        yticks = sorted(set(int(count) for count in counts if count > 0))
        ax.set_yticks(yticks)
        
        # Mostra griglia solo sui tick presenti (quindi solo dove ci sono barre)
        ax.grid(True, axis='y', which='major')
        plots['duration_distribution'] = plot_to_base64(fig)

    # Distribuzione Brani per Artista (a torta)
    total_tracks = df['artist'].value_counts().sum()
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.pie(artist_count, labels=artist_count.index, autopct=lambda p: f'{p:.1f}%' if p > 0 else '',
           startangle=90, colors=['blue', 'green', 'red', 'purple', 'orange'])
    ax.set_title('Distribuzione Brani per Artista')
    plots['artist_distribution'] = plot_to_base64(fig)

    # Evoluzione della Popolarità nel Tempo
    popularity_data = []
    for track in tracks:
        track_info = track.get('track', None)
        if not track_info:
            continue
        album_info = track_info.get('album', None)
        if not album_info:
            continue
        release_date = album_info.get('release_date', '')
        popularity = track_info.get('popularity', None)
        if release_date and popularity is not None:
            year = release_date[:4]
            try:
                year = int(year)
                popularity_data.append({'year': year, 'popularity': popularity})
            except ValueError:
                continue

    if popularity_data:
        df_pop = pd.DataFrame(popularity_data)
        df_pop = df_pop.groupby('year').mean().reset_index()

        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(df_pop['year'], df_pop['popularity'], marker='o', color='cyan', linewidth=2)
        ax.set_title('Evoluzione della Popolarità nel Tempo')
        ax.set_xlabel('Anno di Pubblicazione')
        ax.set_ylabel('Popolarità Media')
        ax.grid(True)
        plots['popularity_over_time'] = plot_to_base64(fig)

    # Distribuzione Temporale dei Brani (numero di brani per anno)
    year_data = []
    for track in tracks:
        track_info = track.get('track', None)
        if not track_info:
            continue
        release_date = track_info.get('album', {}).get('release_date', '')
        if release_date:
            year = release_date[:4]
            try:
                year = int(year)
                year_data.append(year)
            except ValueError:
                continue

    if year_data:
        df_years = pd.Series(year_data).value_counts().sort_index()
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.bar(df_years.index, df_years.values, color='teal')
        ax.set_title('Distribuzione Temporale dei Brani')
        ax.set_xlabel('Anno di Pubblicazione')
        ax.set_ylabel('Numero di Brani')
        ax.grid(True, axis='y')
        plots['track_distribution_by_year'] = plot_to_base64(fig)

    return plots