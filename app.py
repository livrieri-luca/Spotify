from flask import Flask
from flask_login import LoginManager
from blueprints.auth import auth_bp
from blueprints.home import home_bp
from blueprints.search import search_bp

app = Flask(__name__)
app.secret_key = 'chiave_per_session'

# Registriamo i Blueprint
app.register_blueprint(auth_bp)
app.register_blueprint(home_bp)
app.register_blueprint(search_bp)

# Inizializziamo il login manager
login_manager = LoginManager()
login_manager.init_app(app)

if __name__ == '__main__':
    app.run(debug=True)
