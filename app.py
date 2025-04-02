from flask import Flask
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from models import db, User
from blueprints.auth import auth_bp
from blueprints.home import home_bp

app = Flask(__name__)

# Configurazione dell'app
app.secret_key = 'chiave_per_session'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disabilita il monitoraggio delle modifiche, per evitare warning

# Inizializzazione delle estensioni
db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'  # La vista da usare per il login

# Caricamento dell'utente
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))  # Restituisce l'utente in base all'ID

# Registrazione dei Blueprint
app.register_blueprint(auth_bp)
app.register_blueprint(home_bp)

# Creazione del database (se non esiste)
with app.app_context():
    db.create_all()

# Avvio dell'app
if __name__ == '__main__':
    app.run(debug=True)
