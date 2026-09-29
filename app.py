import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'arman_panel_secret_key_123'

# Database initialization function
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            balance REAL DEFAULT 0.0
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
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_input = request.form.get('email')
        password = request.form.get('password')

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ? OR username = ?", (login_input, login_input))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[3], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            return redirect(url_for('dashboard'))
        else:
            flash('Ghalat Email/Username ya Password! Dubara koshish karein.', 'danger')
            
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        hashed_password = generate_password_hash(password)

        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", 
                           (username, email, hashed_password))
            conn.commit()
            conn.close()
            flash('Account kamyaabi se ban gaya! Ab login karein.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Yeh Email ya Username pehle se mojood hai!', 'danger')

    return render_template('signup.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Get user balance
    cursor.execute("SELECT balance FROM users WHERE id = ?", (session['user_id'],))
    user_data = cursor.fetchone()
    balance = user_data[0] if user_data else 0.0
    
    if request.method == 'POST':
        service = request.form.get('service')
        link = request.form.get('link')
        quantity = request.form.get('quantity')
        if service and link and quantity:
            cursor.execute("INSERT INTO orders (user_id, service, link, quantity, price) VALUES (?, ?, ?, ?, ?)",
                           (session['user_id'], service, link, int(quantity), 0.0))
            conn.commit()
            flash('Order kamyaabi se place ho gaya!', 'success')
    
    # Get recent orders
    cursor.execute("SELECT id, service, quantity, status FROM orders WHERE user_id = ?", (session['user_id'],))
    orders = cursor.fetchall()
    conn.close()
    
    return render_template('dashboard.html', username=session.get('username'), balance=balance, orders=orders)

@app.route('/add-funds')
def add_funds():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('add_funds.html', username=session.get('username'))

@app.route('/services')
def services():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('services.html', username=session.get('username'))

@app.route('/orders')
def orders():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, service, link, quantity, price, status FROM orders WHERE user_id = ?", (session['user_id'],))
    orders = cursor.fetchall()
    conn.close()
    return render_template('orders.html', username=session.get('username'), orders=orders)

@app.route('/mass-order')
def mass_order():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('mass_order.html', username=session.get('username'))

@app.route('/support-tickets')
def support_tickets():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('support.html', username=session.get('username'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
