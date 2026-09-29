import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'arman_smm_panel_secure_key_2026'

SERVICES_LIST = [
    {"id": 4317, "name": "Hostinger Premium Plan | Domain + Hosting 1 Year Plan", "category": "Hostinger Domain + Hosting", "rate": 4999, "min": 1, "max": 1},
    {"id": 1, "name": "Instagram Followers [Low Drop] | Premium", "category": "Instagram Followers", "rate": 450, "min": 10, "max": 20000},
    {"id": 2, "name": "Instagram Followers [Real - Mix Data]", "category": "Instagram Followers", "rate": 350, "min": 50, "max": 50000},
    {"id": 3, "name": "TikTok Views [Super Fast]", "category": "TikTok", "rate": 30, "min": 100, "max": 5000000},
    {"id": 4, "name": "TikTok Followers [Real Looking]", "category": "TikTok", "rate": 850, "min": 50, "max": 20000},
    {"id": 5, "name": "YouTube Subscribers [Lifetime Guarantee]", "category": "YouTube", "rate": 3500, "min": 50, "max": 5000}
]

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                balance REAL DEFAULT 162.95,
                total_spent REAL DEFAULT 52.05
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                service TEXT,
                link TEXT,
                quantity INTEGER,
                price REAL,
                status TEXT DEFAULT 'Pending'
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                subject TEXT,
                message TEXT,
                status TEXT DEFAULT 'Open'
            )
        ''')
        conn.commit()
        conn.close()
    except Exception as e:
        print("DB Init Error:", e)

init_db()

def get_user_data(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        return row
    except:
        return None

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_input = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ? OR username = ?", (login_input, login_input))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('dashboard'))
        else:
            flash('Ghalat Email/Username ya Password!', 'danger')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not username or not email or not password:
            flash('Tamam fields bharna lazmi hain!', 'danger')
        else:
            hashed_password = generate_password_hash(password)
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO users (username, email, password, balance, total_spent) VALUES (?, ?, ?, ?, ?)", 
                               (username, email, hashed_password, 162.95, 52.05))
                conn.commit()
                conn.close()
                flash('Account ban gaya! Ab login karein.', 'success')
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                flash('Yeh Email ya Username pehle se mojood hai!', 'danger')
    return render_template('signup.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = get_user_data(session['user_id'])

    if request.method == 'POST':
        service_id = request.form.get('service_id')
        link = request.form.get('link')
        quantity_str = request.form.get('quantity')
        
        if service_id and link and quantity_str:
            try:
                quantity = int(quantity_str)
                selected_service = next((s for s in SERVICES_LIST if s['id'] == int(service_id)), None)
                if selected_service:
                    total_price = (quantity * selected_service['rate']) / 1000.0 if selected_service['min'] > 1 else selected_service['rate']
                    
                    if user['balance'] >= total_price:
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute("UPDATE users SET balance = balance - ?, total_spent = total_spent + ? WHERE id = ?", (total_price, total_price, session['user_id']))
                        cursor.execute("INSERT INTO orders (user_id, service, link, quantity, price, status) VALUES (?, ?, ?, ?, ?, ?)",
                                       (session['user_id'], f"[{selected_service['id']}] {selected_service['name']}", link, quantity, total_price, 'Pending'))
                        conn.commit()
                        conn.close()
                        flash(f'Order place ho gaya! Total: PKR Rs. {total_price:.2f}', 'success')
                    else:
                        flash('Aapke account mein balance kam hai!', 'danger')
            except Exception as e:
                flash(f'Error: {str(e)}', 'danger')
            return redirect(url_for('dashboard'))

    return render_template('dashboard.html', services=SERVICES_LIST, user=user)

@app.route('/services')
def services():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = get_user_data(session['user_id'])
    return render_template('services.html', services=SERVICES_LIST, user=user)

@app.route('/orders')
def orders():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, service, link, quantity, price, status FROM orders WHERE user_id = ? ORDER BY id DESC", (session['user_id'],))
        orders_list = cursor.fetchall()
        conn.close()
    except:
        orders_list = []
    user = get_user_data(session['user_id'])
    return render_template('orders.html', orders=orders_list, user=user)

@app.route('/addfunds')
def add_funds():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = get_user_data(session['user_id'])
    return render_template('add_funds.html', user=user)

@app.route('/support-tickets', methods=['GET', 'POST'])
def support_tickets():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()
        if subject and message:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO tickets (user_id, subject, message, status) VALUES (?, ?, ?, ?)",
                           (session['user_id'], subject, message, 'Open'))
            conn.commit()
            conn.close()
            flash('Ticket submit ho gayi!', 'success')
        return redirect(url_for('support_tickets'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, subject, message, status FROM tickets WHERE user_id = ? ORDER BY id DESC", (session['user_id'],))
        tickets = cursor.fetchall()
        conn.close()
    except:
        tickets = []
    user = get_user_data(session['user_id'])
    return render_template('support.html', tickets=tickets, user=user)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
