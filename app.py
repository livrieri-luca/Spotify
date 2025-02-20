from flask import Flask
from blueprints.auth import auth_bp
from blueprints.home import home_bp
from blueprints.search import search_bp  # Importiamo il blueprint della ricerca

app = Flask(__name__)
app.secret_key = 'chiave_per_session'

# Registriamo i Blueprint
app.register_blueprint(auth_bp)
app.register_blueprint(home_bp)
app.register_blueprint(search_bp)  # Registriamo la ricerca

if __name__ == '__main__':
    app.run(debug=True)
