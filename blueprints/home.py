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

@home_bp.route('/recommendations', methods=['GET', 'POST'])
def get_recommendations():
    """Ottiene suggerimenti musicali basati su input dell'utente"""
    sp = get_spotify_client()
    
    if request.method == 'POST':
        # Recupera i parametri dal form
        seed_artists = request.form.get('seed_artists', '').split(',')
        seed_tracks = request.form.get('seed_tracks', '').split(',')
        seed_genres = request.form.get('seed_genres', '').split(',')
        
        # Filtra i valori vuoti
        seed_artists = [a.strip() for a in seed_artists if a.strip()]
        seed_tracks = [t.strip() for t in seed_tracks if t.strip()]
        seed_genres = [g.strip() for g in seed_genres if g.strip()]
        
        try:
            # Ottieni le raccomandazioni
            recommendations = sp.recommendations(
                seed_artists=seed_artists[:5],  # Spotify accetta max 5 seed
                seed_tracks=seed_tracks[:5],
                seed_genres=seed_genres[:5],
                limit=20
            )
            
            # Se l'utente è autenticato, recupera le sue playlist
            user_playlists = []
            if 'token_info' in session:
                user_playlists = sp.current_user_playlists(limit=50)['items']
            
            return render_template('recommendations.html', 
                                tracks=recommendations['tracks'],
                                user_playlists=user_playlists,
                                seeds={'artists': seed_artists, 
                                      'tracks': seed_tracks, 
                                      'genres': seed_genres})
            
        except Exception as e:
            flash(f"Errore nel recuperare i suggerimenti: {str(e)}", "danger")
            return redirect(url_for('home.get_recommendations'))
    
    # Se è una richiesta GET, mostra il form di ricerca
    return render_template('recommendations_form.html')

@home_bp.route('/save_recommendations', methods=['POST'])
def save_recommendations():
    """Salva i brani consigliati in una playlist"""
    if 'token_info' not in session:
        flash("Devi effettuare l'accesso con Spotify per salvare i suggerimenti", "warning")
        return redirect(url_for('home.search_playlist'))
    
    sp = spotipy.Spotify(auth=session['token_info']['access_token'])
    track_uris = request.form.getlist('track_uris')
    
    if not track_uris:
        flash("Nessun brano selezionato", "warning")
        return redirect(url_for('home.search'))
    
    try:
        # Crea una nuova playlist
        user_id = sp.current_user()['id']
        playlist_name = "Raccomandazioni da ricerca - " + datetime.now().strftime("%d/%m/%Y")
        new_playlist = sp.user_playlist_create(
            user=user_id,
            name=playlist_name,
            public=True,
            description="Brani raccomandati basati sulla tua ricerca"
        )
        
        # Aggiungi i brani
        sp.playlist_add_items(new_playlist['id'], track_uris)
        
        flash(f"{len(track_uris)} brani salvati in una nuova playlist!", "success")
        return redirect(url_for('home.view_playlist', playlist_id=new_playlist['id']))
    
    except Exception as e:
        flash(f"Errore nel salvataggio: {str(e)}", "danger")
        return redirect(url_for('home.search'))
def get_spotify_client():
    """Restituisce un client Spotify autenticato oppure un client pubblico se l'utente non è loggato."""
    token_info = session.get('token_info')
    if token_info:
        return spotipy.Spotify(auth=token_info['access_token'])
    return sp_public
@home_bp.route('/view_playlist/<playlist_id>')
def view_playlist(playlist_id):
    """Visualizza i dettagli di una playlist (brani, descrizione, etc.)"""
    token_info = session.get('token_info')

    # Se l'utente è loggato, utilizza il suo client Spotify autenticato
    sp = get_spotify_client()

    try:
        # Recupera i dettagli della playlist
        playlist = sp.playlist(playlist_id)
        tracks = playlist['tracks']['items']  # Brani della playlist
        playlist_name = playlist['name']
        share_url = playlist['external_urls']['spotify']  # Link per la condivisione

        # Passa i dettagli della playlist e i brani alla template
        return render_template('playlist_details.html', 
                               playlist_name=playlist_name, 
                               tracks=tracks, 
                               share_url=share_url)

    except Exception as e:
        print(f"Errore nel recupero della playlist {playlist_id}: {e}")
        flash("Errore nel recupero della playlist.", "danger")
        return redirect(url_for('home.homepage'))