from flask import Flask
from blueprints.auth import auth_bp
from blueprints.home import home_bp

app = Flask(__name__)
app.secret_key = 'chiavesessione'

# Registro i blueprint
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(home_bp, url_prefix='/home')

if __name__ == "__main__":
    app.run(debug=True)
