from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
import sqlite3
import json
from werkzeug.security import generate_password_hash, check_password_hash
import requests
from apscheduler.schedulers.background import BackgroundScheduler
import os
from datetime import datetime, timedelta
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import asyncio
from threading import Thread
import random
import string

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'

# Telegram Bot Configuration
TELEGRAM_TOKEN = '7628778950:AAGJ3cvrNSlWVqsbU1PUheJshV5yD4xFoFo'
bot = Bot(token=TELEGRAM_TOKEN)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.start()

# Store temporary verification codes
verification_codes = {}

def generate_verification_code():
    """Generate a 6-digit verification code"""
    return ''.join(random.choices(string.digits, k=6))

class User(UserMixin):
    def __init__(self, id, email, telegram_chat_id=None):
        self.id = id
        self.email = email
        self.telegram_chat_id = telegram_chat_id

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect('gratitude.db')
    c = conn.cursor()
    c.execute('SELECT id, email, telegram_chat_id FROM users WHERE id = ?', (user_id,))
    user_data = c.fetchone()
    conn.close()
    if user_data:
        return User(user_data[0], user_data[1], user_data[2])
    return None

def init_db():
    conn = sqlite3.connect('gratitude.db')
    c = conn.cursor()
    
    # Create users table with telegram_chat_id instead of phone_number
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  email TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  telegram_chat_id TEXT,
                  telegram_username TEXT,
                  verification_code TEXT)''')
    
    # Create gratitude entries table
    c.execute('''CREATE TABLE IF NOT EXISTS gratitude_entries
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER NOT NULL,
                  message TEXT NOT NULL,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')
    
    conn.commit()
    conn.close()

async def send_telegram_message(chat_id, message):
    try:
        await bot.send_message(chat_id=chat_id, text=message)
        return True
    except Exception as e:
        print(f"Error sending Telegram message: {e}")
        return False

async def send_daily_reminder():
    conn = sqlite3.connect('gratitude.db')
    c = conn.cursor()
    c.execute('SELECT id, telegram_chat_id FROM users WHERE telegram_chat_id IS NOT NULL')
    users = c.fetchall()
    conn.close()

    for user_id, chat_id in users:
        message = "🌟 Time for your daily gratitude! What are you grateful for today?"
        await send_telegram_message(chat_id, message)

# Schedule daily reminders
scheduler.add_job(
    lambda: asyncio.run(send_daily_reminder()),
    'cron',
    hour=20,  # 8 PM
    minute=0
)

async def handle_telegram_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    message_text = update.message.text.strip()

    # Check if this is a verification code
    for user_id, (code, email) in verification_codes.items():
        if message_text == code:
            conn = sqlite3.connect('gratitude.db')
            c = conn.cursor()
            c.execute('UPDATE users SET telegram_chat_id = ? WHERE id = ?', (str(chat_id), user_id))
            conn.commit()
            conn.close()
            
            # Remove the verification code
            del verification_codes[user_id]
            
            await send_telegram_message(
                chat_id,
                "✅ Connected successfully! I'll send you daily reminders at 8 PM.\n\n"
                "Try it now - what are you grateful for today? 🌟"
            )
            return

    # Handle regular gratitude messages
    conn = sqlite3.connect('gratitude.db')
    c = conn.cursor()
    c.execute('SELECT id FROM users WHERE telegram_chat_id = ?', (str(chat_id),))
    user_data = c.fetchone()

    if user_data:
        user_id = user_data[0]
        # Save the gratitude entry
        c.execute('INSERT INTO gratitude_entries (user_id, message) VALUES (?, ?)',
                 (user_id, message_text))
        conn.commit()
        
        # Send confirmation
        await send_telegram_message(
            chat_id,
            "✨ Saved! Thanks for sharing your gratitude."
        )
    else:
        await send_telegram_message(
            chat_id,
            "To get started, visit our website and get your connection code!"
        )
    
    conn.close()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to Daily Gratitude! 🌟\n\n"
        "To connect your account, visit our website and get your connection code."
    )

async def run_telegram_bot():
    # Set up Telegram bot handlers
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_telegram_message))
    
    # Start the bot
    await application.initialize()
    await application.start()
    await application.run_polling()

@app.route('/')
@login_required
def home():
    conn = sqlite3.connect('gratitude.db')
    c = conn.cursor()
    c.execute('SELECT message, timestamp FROM gratitude_entries WHERE user_id = ? ORDER BY timestamp DESC', 
              (current_user.id,))
    entries = c.fetchall()
    
    # Check if user has linked Telegram
    c.execute('SELECT telegram_chat_id FROM users WHERE id = ?', (current_user.id,))
    telegram_linked = c.execute('SELECT telegram_chat_id FROM users WHERE id = ?', 
                              (current_user.id,)).fetchone()[0] is not None
    
    conn.close()
    return render_template('index.html', entries=entries, telegram_linked=telegram_linked)

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

@app.route('/get_telegram_code', methods=['POST'])
@login_required
def get_telegram_code():
    # Generate a new verification code
    code = generate_verification_code()
    verification_codes[current_user.id] = (code, current_user.email)
    
    return jsonify({
        'code': code,
        'bot_url': 'https://t.me/Gratefulsmsbot',
        'message': 'Click the button below to open Telegram and send this code to the bot!'
    })

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = sqlite3.connect('gratitude.db')
        c = conn.cursor()
        c.execute('SELECT id, email, password, telegram_chat_id FROM users WHERE email = ?', (email,))
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
        telegram_username = request.form.get('telegram_username')
        
        conn = sqlite3.connect('gratitude.db')
        c = conn.cursor()
        
        try:
            # Generate a verification code
            verification_code = generate_verification_code()
            c.execute('INSERT INTO users (email, password, telegram_username, verification_code) VALUES (?, ?, ?, ?)',
                     (email, generate_password_hash(password), telegram_username, verification_code))
            conn.commit()
            conn.close()
            flash('Registration successful! Please check your email for the verification code.', 'success')
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

@app.route('/check_telegram_status')
@login_required
def check_telegram_status():
    conn = sqlite3.connect('gratitude.db')
    c = conn.cursor()
    c.execute('SELECT telegram_chat_id FROM users WHERE id = ?', (current_user.id,))
    result = c.fetchone()
    conn.close()
    
    return jsonify({'linked': result[0] is not None if result else False})

@app.route('/verify', methods=['POST'])
@login_required
def verify():
    verification_code = request.form.get('verification_code')
    conn = sqlite3.connect('gratitude.db')
    c = conn.cursor()
    
    # Check if the verification code matches
    c.execute('SELECT id FROM users WHERE id = ? AND verification_code = ?', (current_user.id, verification_code))
    user_data = c.fetchone()

    if user_data:
        # Update the user's Telegram account
        c.execute('UPDATE users SET telegram_chat_id = ? WHERE id = ?', (current_user.telegram_chat_id, current_user.id))
        conn.commit()
        flash('Your Telegram account has been linked successfully!', 'success')
    else:
        flash('Invalid verification code. Please try again.', 'error')
    conn.close()
    return redirect(url_for('home'))

def run_flask():
    app.run(debug=True, host='0.0.0.0', port=5011)

if __name__ == '__main__':
    init_db()
    
    # Run Telegram bot in a separate thread
    bot_thread = Thread(target=lambda: asyncio.run(run_telegram_bot()))
    bot_thread.daemon = True
    bot_thread.start()
    
    # Run Flask app in the main thread
    run_flask()
