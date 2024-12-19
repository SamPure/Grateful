from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
import sqlite3
import json
from werkzeug.security import generate_password_hash, check_password_hash
from twilio.rest import Client

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Change this to a secure secret key

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User model
class User(UserMixin):
    def __init__(self, id, email, phone_number=None):
        self.id = id
        self.email = email
        self.phone_number = phone_number

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect('gratitude.db')
    c = conn.cursor()
    c.execute('SELECT id, email, phone_number FROM users WHERE id = ?', (user_id,))
    user_data = c.fetchone()
    conn.close()
    if user_data:
        return User(user_data[0], user_data[1], user_data[2])
    return None

def init_db():
    conn = sqlite3.connect('gratitude.db')
    c = conn.cursor()
    
    # Create users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  email TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  phone_number TEXT)''')
    
    # Create gratitude entries table
    c.execute('''CREATE TABLE IF NOT EXISTS gratitude_entries
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER NOT NULL,
                  message TEXT NOT NULL,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')
    
    conn.commit()
    conn.close()

@app.route('/')
@login_required
def home():
    conn = sqlite3.connect('gratitude.db')
    c = conn.cursor()
    c.execute('SELECT message, timestamp FROM gratitude_entries WHERE user_id = ? ORDER BY timestamp DESC', 
              (current_user.id,))
    entries = c.fetchall()
    conn.close()
    return render_template('index.html', entries=entries)

@app.route('/add_gratitude', methods=['POST'])
@login_required
def add_gratitude():
    message = request.form.get('message')
    if message:
        conn = sqlite3.connect('gratitude.db')
        c = conn.cursor()
        c.execute('INSERT INTO gratitude_entries (user_id, message) VALUES (?, ?)',
                 (current_user.id, message))
        conn.commit()
        conn.close()
        flash('Gratitude entry added successfully!', 'success')
    return redirect(url_for('home'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = sqlite3.connect('gratitude.db')
        c = conn.cursor()
        c.execute('SELECT id, email, password, phone_number FROM users WHERE email = ?', (email,))
        user_data = c.fetchone()
        conn.close()
        
        if user_data and check_password_hash(user_data[2], password):
            user = User(user_data[0], user_data[1], user_data[3])
            login_user(user)
            return redirect(url_for('home'))
        flash('Invalid email or password', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        phone_number = request.form.get('phone_number')
        
        conn = sqlite3.connect('gratitude.db')
        c = conn.cursor()
        
        try:
            c.execute('INSERT INTO users (email, password, phone_number) VALUES (?, ?, ?)',
                     (email, generate_password_hash(password), phone_number))
            conn.commit()
            conn.close()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email already exists', 'error')
            conn.close()
            
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5011)
