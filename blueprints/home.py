# Importiamo i moduli necessari da Flask e SQLAlchemy
from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from sqlalchemy import text
from flask_login import login_required, current_user
from services.spotify_api import (
    sp_public,
    get_spotify_object,
    get_user_info,
    get_user_playlists,
    sp_oauth
)
from models import db, User, SavedPlaylist

home_bp = Blueprint('home', __name__, template_folder='templates')

# Definiamo la rotta per la homepage dell'utente
@home_bp.route('/homepage')
def homepage():
    token_info = session.get('token_info')
    user_sp = None
    user_info = None
    playlists = []

    # Se l'utente non è autenticato ma ha un token Spotify, mostriamo le playlist Spotify
    if token_info and not current_user.is_authenticated:
        sp = get_spotify_object(token_info)
        user_sp = get_user_info(token_info)
        playlists = get_user_playlists(token_info)
        user_info = {'display_name': user_sp['display_name']}

    # Se l'utente è autenticato con Flask ma non ha un token Spotify, mostriamo le playlist salvate
    elif current_user.is_authenticated and not token_info:
        user_info = {'display_name': current_user.username}
        saved = SavedPlaylist.query.filter_by(user_id=current_user.id).all()
        for s in saved:
            try:
                playlists.append(sp_public.playlist(s.playlist_id))
            except Exception as e:
                print(f"Errore nel recupero playlist {s.playlist_id}: {e}")

    # Se l'utente è autenticato e ha un token Spotify, mostriamo entrambe le playlist
    elif token_info and current_user.is_authenticated:
        sp = get_spotify_object(token_info)
        user_sp = get_user_info(token_info)
        playlists = get_user_playlists(token_info)
        user_info = {'display_name': user_sp['display_name']}

        saved = SavedPlaylist.query.filter_by(user_id=current_user.id).all()
        for s in saved:
            try:
                playlist_data = sp_public.playlist(s.playlist_id)
                if not any(pl['id'] == playlist_data['id'] for pl in playlists):
                    playlists.append(playlist_data)
            except Exception as e:
                print(f"Errore nel recupero playlist {s.playlist_id}: {e}")

    # Renderizza la pagina della home con i dati utente e le playlist
    return render_template('home.html', user_sp=user_sp, user_info=user_info, playlists=playlists)

# Definiamo la rotta per la ricerca di playlist
@home_bp.route('/cerca')
def cerca():
    query = request.args.get('query', '')
    results = []
    if query:
        try:
            results = sp_public.search(q=query, type='playlist', limit=10)['playlists']['items']
        except Exception as e:
            flash('Errore nella ricerca delle playlist')
            print(e)
    return render_template('home.html', results=results, user_info=None, playlists=[])

# Definiamo la rotta per salvare una playlist
@home_bp.route('/saved_playlist', methods=['POST'])
def saved_playlist():
    playlist_id = request.form.get('playlist_id')

    if not playlist_id:
        flash('Playlist ID non valido.')
        return redirect(url_for('home.homepage'))

    user_id = current_user.id if current_user.is_authenticated else None

    # Verifica se la playlist è già stata salvata
    existing = SavedPlaylist.query.filter_by(user_id=user_id, playlist_id=playlist_id).first()

    if existing:
        flash('Questa playlist è già stata salvata.')
    else:
        new_playlist = SavedPlaylist(user_id=user_id, playlist_id=playlist_id)
        db.session.add(new_playlist)
        db.session.commit()
        flash('Playlist salvata con successo!')

    return redirect(url_for('home.homepage'))

# Definiamo la rotta per rimuovere tutte le playlist salvate
@home_bp.route('/remove_playlist', methods=['POST'])
@login_required
def remove_playlist():
    SavedPlaylist.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    flash('Tutte le playlist rimosse!')
    return redirect(url_for('home.homepage'))

# Definiamo la rotta per rimuovere una singola playlist salvata
@home_bp.route('/remove_single_playlist', methods=['POST'])
@login_required
def remove_single_playlist():
    playlist_id = request.form.get('playlist_id')
    playlist = SavedPlaylist.query.filter_by(user_id=current_user.id, playlist_id=playlist_id).first()
    if playlist:
        db.session.delete(playlist)
        db.session.commit()
        flash('Playlist rimossa con successo!')
    else:
        flash('Errore: Playlist non trovata.')
    return redirect(url_for('home.homepage'))

# Definiamo la rotta per visualizzare i brani di una playlist
@home_bp.route('/visualizza_brani/<playlist_id>')
def visualizza_brani(playlist_id):
    print(f"Carico la playlist con ID: {playlist_id}")

    token_info = session.get('token_info')
    sp = get_spotify_object(token_info) if token_info else sp_public

    try:
        # Recupera la playlist e i suoi brani
        playlist = sp.playlist(playlist_id)
        print("Nome playlist:", playlist['name'])  # Debug per il nome della playlist
        tracks = playlist['tracks']['items']

        # Ottieni il link della playlist per la condivisione
        share_url = playlist['external_urls']['spotify']  # Link esterno per la condivisione

        return render_template('playlist_tracks.html', tracks=tracks, playlist_name=playlist['name'], share_url=share_url)
    except Exception as e:
        print(f"Errore nel caricamento della playlist {playlist_id}: {e}")
        return redirect(url_for('home.homepage'))

# Definiamo la rotta per visualizzare i brani di una playlist tramite ID
@home_bp.route('/playlist_tracks/<playlist_id>')
def playlist_tracks(playlist_id):
    token_info = session.get('token_info')
    if not token_info:
        return redirect(url_for('auth.loginlocale'))

    sp = get_spotify_object(token_info)
    try:
        # Recupera i brani della playlist tramite Spotify
        playlist_data = sp.playlist_tracks(playlist_id)
        tracks = playlist_data['items']
    except Exception as e:
        print(f"Errore nel recupero dei brani: {e}")
        tracks = []

    return render_template('playlist_tracks.html', tracks=tracks, playlist_id=playlist_id)

# Funzione di supporto per recuperare i brani di una playlist
def get_playlist_tracks(token_info, playlist_id):
    try:
        # Recupera i brani dalla playlist
        results = sp.playlist_tracks(playlist_id)
        return results['items']
    except Exception as e:
        print(f"Errore nel recupero dei brani: {e}")
        return []

# Definiamo la rotta per visualizzare i dettagli di un brano
@home_bp.route('/track/<track_id>')
def track_details(track_id):
    token_info = session.get('token_info')

    if token_info:
        sp = get_spotify_object(token_info)
    else:
        sp = sp_public  # Client pubblico per i non autenticati

    try:
        print(f"Caricamento dettagli per il brano con ID: {track_id}")

        # Recupera i dettagli della traccia e del genere
        track, genre = get_track_details(sp, track_id)

        if track is None:
            print(f"Brano con ID {track_id} non trovato.")
            return render_template('track_details.html', track=None, genre=None)

        return render_template('track_details.html', track=track, genre=genre)
    except Exception as e:
        print(f"Errore nel recupero dei dettagli per la traccia {track_id}: {e}")
        return render_template('track_details.html', track=None, genre=None)

# Funzione di supporto per ottenere i dettagli della traccia
def get_track_details(sp, track_id):
    try:
        # Recupera i dettagli della traccia
        track = sp.track(track_id)

        if not track:
            print(f"Track con ID {track_id} non trovato.")
            return None, 'Genere sconosciuto'

        # Ottieni il genere dell'artista della traccia
        artist_id = track['artists'][0]['id']
        artist = sp.artist(artist_id)

        genres = artist.get('genres', [])
        genre = genres[0] if genres else 'Genere sconosciuto'

        return track, genre
    except Exception as e:
        print(f"Errore nel recupero dettagli per la traccia {track_id}: {e}")
        return None, 'Genere sconosciuto'

# Definiamo la rotta per ottenere raccomandazioni basate su artista, traccia o genere
@home_bp.route('/recommendations', methods=['GET', 'POST'])
def get_recommendations():
    artist_id = request.args.get('artist_id')
    track_id = request.args.get('track_id')
    genre = request.args.get('genre')

    sp = get_spotify_object()

    # Parametri per le raccomandazioni
    params = {
        'seed_artists': artist_id if artist_id else '',
        'seed_tracks': track_id if track_id else '',
        'seed_genres': genre if genre else '',
        'limit': 10
    }

    try:
        recommendations = sp.recommendations(**params)['tracks']
        print(f"Raccomandazioni trovate: {len(recommendations)}")
    except Exception as e:
        print(f"Errore: {e}")
        flash('Errore nel recupero delle raccomandazioni.', 'danger')
        recommendations = []

    return render_template('recommendations.html', recommendations=recommendations)

# Definiamo la rotta per salvare le raccomandazioni come playlist
@home_bp.route('/save_recommendations', methods=['POST'])
@login_required
def save_recommendations():
    sp = get_spotify_object()

    track_ids = request.form.getlist('track_ids')  # Array di track_id passati dal frontend

    user_id = sp.current_user()['id']  # Ottieni l'ID dell'utente
    playlist_name = "Nuova Playlist da Raccomandazioni"
    playlist_description = "Playlist creata automaticamente con i brani consigliati"
    
    try:
        playlist = sp.user_playlist_create(user_id, playlist_name, description=playlist_description)
        playlist_id = playlist['id']

        # Aggiungi i brani alla playlist
        sp.user_playlist_add_tracks(user_id, playlist_id, track_ids)

        flash("Playlist creata e brani salvati con successo!", 'success')
    except Exception as e:
        print(f"Errore durante il salvataggio delle raccomandazioni: {e}")
        flash("Si è verificato un errore durante il salvataggio della playlist.", 'danger')

    return redirect(url_for('home.get_recommendations'))
