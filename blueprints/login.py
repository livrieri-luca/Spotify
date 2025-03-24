from flask import Flask, render_template, redirect, url_for, request
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user


# Creazione dell'app Flask
app = Flask(__name__)

# Impostazione di Flask-Login
app.secret_key = 'your_secret_key'  # Cambia questa chiave segreta
login_manager = LoginManager()
login_manager.init_app(app)

# Simulazione di un database di utenti (dovresti usare un vero database in produzione)
users = {'user1': {'password': 'password123'}}

# Classe User per Flask-Login
class User(UserMixin):
    def __init__(self, id):
        self.id = id

# Funzione di caricamento dell'utente
@login_manager.user_loader
def load_user(user_id):
    if user_id in users:
        return User(user_id)
    return None

# Pagina di login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username]['password'] == password:
            user = User(username)
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            return 'Invalid username or password', 401
    return render_template('login.html')

# Pagina di logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Pagina protetta (richiede il login)
@app.route('/dashboard')
@login_required
def dashboard():
    return f'Welcome to your dashboard, {current_user.id}!'

if __name__ == '__main__':
    app.run(debug=True)

