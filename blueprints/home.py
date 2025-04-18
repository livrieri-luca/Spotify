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



@home_bp.route('/select_playlists_for_comparison', methods=['GET', 'POST'])
@login_required
def select_playlists_for_comparison():
    # Recupera le playlist dell'utente con il nome della playlist
    playlists = db.session.execute(
        text('''
            SELECT p.id, p.name 
            FROM playlist p
            JOIN saved_playlist sp ON p.id = sp.playlist_id
            WHERE sp.user_id = :user_id
        '''),
        {'user_id': current_user.id}
    ).fetchall()

    # Se l'utente ha meno di due playlist, mostra un messaggio
    if len(playlists) < 2:
        flash('Devi avere almeno due playlist per fare un confronto.', 'danger')
        return redirect(url_for('home.homepage'))

    if request.method == 'POST':
        # Recupera gli ID delle playlist selezionate
        playlist_1_id = request.form.get('playlist_1')
        playlist_2_id = request.form.get('playlist_2')

        # Verifica che entrambe le playlist siano selezionate
        if playlist_1_id and playlist_2_id:
            return redirect(url_for('analisi.playlist_analysis', playlist_1_id=playlist_1_id, playlist_2_id=playlist_2_id))

        flash('Seleziona due playlist per il confronto!', 'warning')
    
    return render_template('select_playlists_for_comparison.html', playlists=playlists)



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
        playlist = sp.playlist(playlist_id)
        print("Nome playlist:", playlist['name'])  # ← debug
        tracks = playlist['tracks']['items']
        return render_template('playlist_tracks.html', tracks=tracks, playlist_name=playlist['name'])
    except Exception as e:
        print(f"Errore nel caricamento della playlist {playlist_id}: {e}")
        return redirect(url_for('home.homepage'))




@home_bp.route('/recommendations', methods=['GET', 'POST'])
def recommendations():
    # Controlla se l'utente è autenticato
    token_info = session.get('token_info')
    sp = None
    user_playlists = []

    if token_info:
        sp = get_spotify_object(token_info)  # Ottieni l'oggetto Spotify
        user_playlists = sp.current_user_playlists()['items']  # Ottieni le playlist dell'utente
    else:
        flash('Non sei autenticato. Alcune funzionalità potrebbero non essere disponibili.', 'warning')

    recommendations = []

    if request.method == 'POST' and token_info:  # Fai le raccomandazioni solo se l'utente è loggato
        artist_id = request.form.get('artist_id')
        track_id = request.form.get('track_id')
        genre = request.form.get('genre')
        playlist_id = request.form.get('playlist_id')
        create_new_playlist = request.form.get('create_new_playlist')
        new_playlist_name = request.form.get('new_playlist_name')

        # Parametri per ottenere le raccomandazioni
        params = {
            'seed_artists': artist_id if artist_id else '',
            'seed_tracks': track_id if track_id else '',
            'seed_genres': genre if genre else '',
            'limit': 10
        }

        # Ottieni le raccomandazioni da Spotify
        recommendations = sp.recommendations(**params)['tracks']
        track_uris = [track['uri'] for track in recommendations]

        # Creazione di una nuova playlist, se richiesto
        if create_new_playlist and new_playlist_name:
            user_id = sp.current_user()['id']
            new_playlist = sp.user_playlist_create(user_id, new_playlist_name, public=False)
            playlist_id = new_playlist['id']
            flash(f"Nuova playlist '{new_playlist_name}' creata!", 'success')

        # Aggiungi tracce alla playlist selezionata o nuova
        if playlist_id:
            add_tracks_to_playlist(token_info, playlist_id, track_uris)
            flash('Brani aggiunti alla playlist!', 'success')

    # Renderizza la pagina con le raccomandazioni e le playlist (se l'utente è autenticato)
    return render_template(
        'recommendations.html',
        recommendations=recommendations,
        user_playlists=user_playlists,
        token_info=token_info
    )


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


@home_bp.route('/track_details/<track_id>')
def track_details(track_id):
    # Ottieni il token info dalla sessione
    token_info = session.get('token_info')
    if not token_info:
        return redirect(url_for('auth.loginlocale'))

    # Recupera i dettagli del brano
    track, genre = get_track_details(token_info, track_id)
    
    # Se il brano non viene trovato, ritorna un errore
    if not track:
        flash("Brano non trovato!", "danger")
        return redirect(url_for('home.homepage'))

    # Ottieni l'ID della playlist dai parametri
    playlist_id = request.args.get('playlist_id')

    # Rendi il template con i dettagli del brano
    return render_template('track_details.html', track=track, genre=genre, playlist_id=playlist_id)


def get_playlist_tracks(token_info, playlist_id):
    try:
        # Fetch the tracks from the specified playlist
        results = sp.playlist_tracks(playlist_id)
        return results['items']
    except Exception as e:
        print(f"Error fetching playlist tracks: {e}")
        return []

def get_track_details(token_info, track_id):
    try:
        # Fetch track details from the Spotify API
        track = sp.track(track_id)
        
        if track is None or 'artists' not in track or len(track['artists']) == 0:
            return None, []  # Return empty or default values if no valid track found
        
        # Assuming genre info is fetched from the track's album
        genre = track['album']['artists'][0].get('genres', [])
        
        return track, genre
    except Exception as e:
        print(f"Error fetching track details: {e}")
        return None, []
