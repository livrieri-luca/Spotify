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
    # Recupera le playlist dell'utente
    playlists = db.session.execute(
        text('SELECT playlist_id FROM saved_playlist WHERE user_id = :user_id'),
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


from flask import request, redirect, url_for, flash

@home_bp.route('/saved_playlist', methods=['POST'])
def saved_playlist():
    playlist_id = request.form.get('playlist_id')

    if not playlist_id:
        flash('Playlist ID non valido.')
        return redirect(url_for('home.cerca'))

    # Logica per salvare la playlist nel database
    # Assumendo che tu abbia un modello per le playlist salvate dell'utente
    user_id = current_user.id  # Se l'utente è loggato, prendi il suo ID

    # Controlla se la playlist è già stata salvata dall'utente
    existing_playlist = Playlist.query.filter_by(user_id=user_id, spotify_id=playlist_id).first()

    if existing_playlist:
        flash('Questa playlist è già stata salvata.')
    else:
        # Aggiungi la playlist al database
        new_playlist = Playlist(user_id=user_id, spotify_id=playlist_id)
        db.session.add(new_playlist)
        db.session.commit()
        flash('Playlist salvata con successo.')

    return redirect(url_for('home.cerca'))  # Torna alla pagina dei risultati di ricerca



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
    token_info = session.get('token_info')
    sp = get_spotify_object(token_info) if token_info else sp_public

    try:
        playlist = sp.playlist(playlist_id)
        tracks = playlist['tracks']['items']
        return render_template('brani.html', tracks=tracks, playlist_name=playlist['name'])
    except Exception as e:
        print(f"Errore caricamento playlist {playlist_id}: {e}")
        return redirect(url_for('home.homepage'))


@home_bp.route('/albuminfo/<album_id>')
def albuminfo(album_id):
    sp = get_spotify_object(session.get('token_info')) if session.get('token_info') else sp_public
    try:
        album = sp.album(album_id)
        album_data = {
            "name": album['name'],
            "release_date": album['release_date'],
            "total_tracks": album['total_tracks'],
            "image": album['images'][0]['url'] if album['images'] else None,
            "artists": [{"name": a["name"], "id": a["id"]} for a in album["artists"]],
            "tracks": [{"name": t["name"], "duration_ms": t["duration_ms"]} for t in album["tracks"]["items"]]
        }
        return render_template('albuminfo.html', album_data=album_data)
    except Exception as e:
        print(f"Errore caricamento album {album_id}: {e}")
        return redirect(url_for('home.homepage'))


@home_bp.route('/artistinfo/<artist_id>')
def artistinfo(artist_id):
    sp = get_spotify_object(session.get('token_info')) if session.get('token_info') else sp_public
    try:
        artist = sp.artist(artist_id)
        top_tracks = sp.artist_top_tracks(artist_id, country='IT')['tracks']
        albums = sp.artist_albums(artist_id, album_type='album', country='IT')['items']
        artist_data = {
            "name": artist['name'],
            "genres": artist.get('genres', []),
            "image": artist['images'][0]['url'] if artist['images'] else None,
            "top_tracks": [{"name": t["name"], "preview_url": t["preview_url"]} for t in top_tracks],
            "albums": [{"name": a["name"], "image": a["images"][0]['url']} for a in albums]
        }
        return render_template('artistinfo.html', artist_data=artist_data)
    except Exception as e:
        print(f"Errore info artista {artist_id}: {e}")
        return redirect(url_for('home.homepage'))

@home_bp.route('/recommendations', methods=['GET', 'POST'])
@login_required
def recommendations():
    token_info = session.get('token_info')
    if not token_info:
        return redirect(url_for('auth.login'))
    
    sp = get_spotify_object(token_info)
    user_playlists = sp.current_user_playlists()['items']
    
    recommendations = []

    if request.method == 'POST':
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

    return render_template('recommendations.html', recommendations=recommendations, user_playlists=user_playlists)

@home_bp.route('/playlist_tracks/<playlist_id>')
def playlist_tracks(playlist_id):
     token_info = session.get('token_info')
     
     if token_info:
         sp = get_spotify_object(token_info)
     else:
         sp = sp_public  # Usa accesso pubblico se l'utente non ha fatto login a Spotify
 
     try:
         playlist = sp.playlist(playlist_id)
         tracks = playlist['tracks']['items']
         playlist_name = playlist['name']
         return render_template('playlist_tracks.html', tracks=tracks, playlist_name=playlist_name)
     except Exception as e:
         print(f"Errore nel caricamento della playlist {playlist_id}: {e}")
         return redirect(url_for('home.homepage'))  # Fallback in caso di errore