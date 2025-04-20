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
# Funzione per selezionare due playlist da confrontare


@home_bp.route('/homepage')
def homepage():
    token_info = session.get('token_info')
    user_sp = None
    user_info = None
    playlists = []

    if token_info and not current_user.is_authenticated:
        # Solo Spotify
        sp = get_spotify_object(token_info)
        user_sp = get_user_info(token_info)
        playlists = get_user_playlists(token_info)
        user_info = {'display_name': user_sp['display_name']}

    elif current_user.is_authenticated and not token_info:
        # Solo Flask
        user_info = {'display_name': current_user.username}
        saved = SavedPlaylist.query.filter_by(user_id=current_user.id).all()
        for s in saved:
            try:
                playlists.append(sp_public.playlist(s.playlist_id))
            except Exception as e:
                print(f"Errore nel recupero playlist {s.playlist_id}: {e}")

    elif token_info and current_user.is_authenticated:
        # Entrambi
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

    return render_template('home.html', user_sp=user_sp, user_info=user_info, playlists=playlists)


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
# 

@home_bp.route('/saved_playlist', methods=['POST'])
def saved_playlist():
    playlist_id = request.form.get('playlist_id')

    if not playlist_id:
        flash('Playlist ID non valido.')
        return redirect(url_for('home.homepage'))

    user_id = current_user.id if current_user.is_authenticated else None

    # Controlla se la playlist è già stata salvata da questo utente o in generale (se user_id è None)
    existing = SavedPlaylist.query.filter_by(user_id=user_id, playlist_id=playlist_id).first()

    if existing:
        flash('Questa playlist è già stata salvata.')
    else:
        new_playlist = SavedPlaylist(user_id=user_id, playlist_id=playlist_id)
        db.session.add(new_playlist)
        db.session.commit()
        flash('Playlist salvata con successo!')

    return redirect(url_for('home.homepage'))




@home_bp.route('/remove_playlist', methods=['POST'])
@login_required
def remove_playlist():
    SavedPlaylist.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    flash('Tutte le playlist rimosse!')
    return redirect(url_for('home.homepage'))


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

@home_bp.route('/visualizza_brani/<playlist_id>')
def visualizza_brani(playlist_id):
    print(f"Carico la playlist con ID: {playlist_id}")

    token_info = session.get('token_info')
    sp = get_spotify_object(token_info) if token_info else sp_public

    try:
        # Recupera la playlist da Spotify
        playlist = sp.playlist(playlist_id)
        print("Nome playlist:", playlist['name'])  # Debug per il nome della playlist
        tracks = playlist['tracks']['items']

        # Ottieni il link della playlist su Spotify (per la condivisione)
        share_url = playlist['external_urls']['spotify']  # Link esterno per la condivisione

        # Passa il link della playlist al template
        return render_template('playlist_tracks.html', tracks=tracks, playlist_name=playlist['name'], share_url=share_url)
    except Exception as e:
        print(f"Errore nel caricamento della playlist {playlist_id}: {e}")
        return redirect(url_for('home.homepage'))



@home_bp.route('/playlist_tracks/<playlist_id>')
def playlist_tracks(playlist_id):
    # Ottieni le informazioni del token dalla sessione
    token_info = session.get('token_info')
    if not token_info:
        return redirect(url_for('auth.loginlocale'))

    sp = get_spotify_object(token_info)
    try:
        # Recupera i brani dalla playlist tramite l'API di Spotify
        playlist_data = sp.playlist_tracks(playlist_id)
        tracks = playlist_data['items']
    except Exception as e:
        print(f"Errore nel recupero dei brani: {e}")
        tracks = []

    # Passa i brani al template
    return render_template('playlist_tracks.html', tracks=tracks, playlist_id=playlist_id)


def get_playlist_tracks(token_info, playlist_id):
    try:
        # Fetch the tracks from the specified playlist
        results = sp.playlist_tracks(playlist_id)
        return results['items']
    except Exception as e:
        print(f"Error fetching playlist tracks: {e}")
        return []

@home_bp.route('/track/<track_id>')
def track_details(track_id):
    token_info = session.get('token_info')
    
    # Verifica se c'è un token, altrimenti usa il client pubblico
    if token_info:
        sp = get_spotify_object(token_info)
    else:
        sp = sp_public  # Client pubblico per i non autenticati
    
    try:
        # Loggare l'ID della traccia per debug
        print(f"Caricamento dettagli per il brano con ID: {track_id}")

        # Recupera i dettagli della traccia e del genere
        track, genre = get_track_details(sp, track_id)

        # Se la traccia non è stata trovata, torna con un messaggio
        if track is None:
            print(f"Brano con ID {track_id} non trovato.")
            return render_template('track_details.html', track=None, genre=None)

        # Invia i dettagli al template
        return render_template('track_details.html', track=track, genre=genre)
    except Exception as e:
        # Gestisci errori generali e logga il problema
        print(f"Errore nel recupero dei dettagli per la traccia {track_id}: {e}")
        return render_template('track_details.html', track=None, genre=None)

def get_track_details(sp, track_id):
    try:
        # Ottieni i dettagli della traccia da Spotify
        track = sp.track(track_id)
        
        # Se la traccia non è trovata, ritorna None
        if not track:
            print(f"Track con ID {track_id} non trovato.")
            return None, 'Genere sconosciuto'
        
        # Ottieni l'ID dell'artista dalla traccia
        artist_id = track['artists'][0]['id']
        artist = sp.artist(artist_id)
        
        # Ottieni i generi dell'artista
        genres = artist.get('genres', [])
        genre = genres[0] if genres else 'Genere sconosciuto'

        # Ritorna la traccia e il genere
        return track, genre
    except Exception as e:
        print(f"Errore nel recupero dettagli per la traccia {track_id}: {e}")
        return None, 'Genere sconosciuto'


# Funzione per ottenere le raccomandazioni e aggiungere i brani
@home_bp.route('/recommendations', methods=['GET', 'POST'])
def get_recommendations():
    token_info = session.get('token_info')  # Ottieni il token dalla sessione
    sp = None
    recommendations = []

    # Verifica se l'utente è autenticato
    if token_info:
        sp = get_spotify_object(token_info)
    else:
        flash('Devi effettuare il login su Spotify per ottenere le raccomandazioni.', 'warning')
    
    if request.method == 'POST' and token_info:
        # Ottieni i parametri dal form
        artist_id = request.form.get('artist_id')
        track_id = request.form.get('track_id')
        genre = request.form.get('genre')
        playlist_id = request.form.get('saved_playlist_id')  # ID della playlist salvata
        create_new_playlist = request.form.get('create_new_playlist')
        new_playlist_name = request.form.get('new_playlist_name')

        # Parametri per la richiesta delle raccomandazioni
        params = {
            'seed_artists': artist_id if artist_id else '',
            'seed_tracks': track_id if track_id else '',
            'seed_genres': genre if genre else '',
            'limit': 10
        }

        print(f"Params per raccomandazioni: {params}")  # Debug: Controlla i parametri

        try:
            # Ottenere le raccomandazioni da Spotify
            recommendations = sp.recommendations(**params)['tracks'] if sp else []
            print(f"Raccomandazioni ricevute: {recommendations}")  # Debug: Controlla le raccomandazioni

            track_uris = [track['uri'] for track in recommendations]  # Estrai gli URI dei brani

            # Se l'utente è autenticato e ha selezionato una playlist per aggiungere i brani
            if playlist_id:
                add_tracks_to_playlist(token_info, playlist_id, track_uris)
                flash('Brani aggiunti alla playlist!', 'success')

            # Se l'utente ha scelto di creare una nuova playlist
            if create_new_playlist and new_playlist_name:
                user_id = sp.current_user()['id']
                new_playlist = sp.user_playlist_create(user_id, new_playlist_name, public=False)
                playlist_id = new_playlist['id']
                flash(f"Nuova playlist '{new_playlist_name}' creata!", 'success')

        except Exception as e:
            print(f"Errore durante la richiesta delle raccomandazioni: {e}")  # Debug: Gestione errori

    return render_template(
        'recommendations.html',
        recommendations=recommendations,
        token_info=token_info
    )

# Funzione per aggiungere i brani alla playlist
def add_tracks_to_playlist(token_info, playlist_id, track_uris):
    try:
        sp = get_spotify_object(token_info)
        sp.playlist_add_items(playlist_id, track_uris)  # Aggiungi i brani alla playlist
    except Exception as e:
        print(f"Errore nell'aggiungere brani alla playlist: {e}")
        flash('Errore nell\'aggiungere i brani alla playlist.', 'danger')