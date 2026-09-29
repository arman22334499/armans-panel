import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

app.secret_key = 'arman_simple_smm_key_2026'
app.permanent_session_lifetime = 3600

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('DROP TABLE IF EXISTS users')
        cursor.execute('DROP TABLE IF EXISTS orders')
        
        cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                balance REAL DEFAULT 100.0,
                total_spent REAL DEFAULT 0.0,
                is_admin INTEGER DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE orders (
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
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                rate REAL NOT NULL
            )
        ''')
        
        cursor.execute("SELECT COUNT(*) FROM services")
        if cursor.fetchone()[0] == 0:
            default_services = [
                ("Instagram Followers [Fast]", "Instagram", 350.0),
                ("Instagram Likes", "Instagram", 150.0),
                ("TikTok Views", "TikTok", 50.0),
                ("TikTok Followers", "TikTok", 800.0),
                ("YouTube Subscribers", "YouTube", 3500.0)
            ]
            cursor.executemany("INSERT INTO services (name, category, rate) VALUES (?, ?, ?)", default_services)

        admin_pass = generate_password_hash('admin123')
        cursor.execute("INSERT INTO users (username, email, password, balance, total_spent, is_admin) VALUES (?, ?, ?, ?, ?, ?)",
                       ('admin', 'admin@armansmm.com', admin_pass, 5000.0, 0.0, 1))
        
        conn.commit()
        conn.close()
        print("Database re-initialized successfully at:", DB_PATH)
    except Exception as e:
        print("CRITICAL DB Error:", e)

init_db()

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('admin_panel' if session.get('is_admin') == 1 else 'dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_input = request.form.get('email', '') or request.form.get('username', '')
        login_input = login_input.strip()
        password = request.form.get('password', '')

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ? OR username = ?", (login_input, login_input))
            user = cursor.fetchone()
            conn.close()

            if user and check_password_hash(user['password'], password):
                session.clear()
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['is_admin'] = user['is_admin']
                session.permanent = True
                
                if user['is_admin'] == 1:
                    return redirect(url_for('admin_panel'))
                return redirect(url_for('dashboard'))
            else:
                flash('Ghalat Email/Username ya Password!', 'danger')
        except Exception as e:
            flash(f'Login Error: {str(e)}', 'danger')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not username or not email or not password:
            flash('Tamam fields bharna lazmi hain!', 'danger')
            return redirect(url_for('signup'))
        
        try:
            hashed_password = generate_password_hash(password)
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username, email))
            if cursor.fetchone():
                flash('Yeh Email ya Username pehle se mojood hai!', 'danger')
                conn.close()
                return redirect(url_for('signup'))

            cursor.execute("INSERT INTO users (username, email, password, balance, total_spent, is_admin) VALUES (?, ?, ?, ?, ?, ?)", 
                           (username, email, hashed_password, 100.0, 0.0, 0))
            conn.commit()
            conn.close()
            flash('Account ban gaya! Ab aap login kar sakte hain.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'Signup Error: {str(e)}', 'danger')
            return redirect(url_for('signup'))
            
    return render_template('signup.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
    user = cursor.fetchone()
    
    cursor.execute("SELECT * FROM services")
    services = cursor.fetchall()
    
    if request.method == 'POST':
        service_id = request.form.get('service_id')
        link = request.form.get('link')
        quantity = int(request.form.get('quantity', 0))
        
        cursor.execute("SELECT * FROM services WHERE id = ?", (service_id,))
        srv = cursor.fetchone()
        
        if srv and quantity > 0:
            price = (quantity * srv['rate']) / 1000.0
            if user['balance'] >= price:
                cursor.execute("UPDATE users SET balance = balance - ?, total_spent = total_spent + ? WHERE id = ?", (price, price, user['id']))
                cursor.execute("INSERT INTO orders (user_id, service, link, quantity, price, status) VALUES (?, ?, ?, ?, ?, ?)",
                               (user['id'], srv['name'], link, quantity, price, 'Pending'))
                conn.commit()
                flash('Order kamyabi se place ho gaya!', 'success')
            else:
                flash('Balance kam hai!', 'danger')
        conn.close()
        return redirect(url_for('dashboard'))
    
    conn.close()
    return render_template('dashboard.html', user=user, services=services)

@app.route('/add_funds', methods=['GET', 'POST'])
def add_funds():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    flash('Funds adding feature jald araha hai!', 'info')
    return redirect(url_for('dashboard'))

@app.route('/orders')
def orders():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
    user = cursor.fetchone()
    cursor.execute("SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC", (session['user_id'],))
    user_orders = cursor.fetchall()
    conn.close()
    return render_template('orders.html', user=user, orders=user_orders)

@app.route('/services')
def services():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
    user = cursor.fetchone()
    cursor.execute("SELECT * FROM services")
    all_services = cursor.fetchall()
    conn.close()
    return render_template('services.html', user=user, services=all_services)

@app.route('/admin')
def admin_panel():
    if 'user_id' not in session or session.get('is_admin') != 1:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
    user = cursor.fetchone()
    cursor.execute("SELECT * FROM orders ORDER BY id DESC")
    all_orders = cursor.fetchall()
    conn.close()
    return render_template('admin.html', user=user, all_orders=all_orders)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
