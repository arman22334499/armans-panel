from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import requests
import os

app = Flask(__name__)
app.secret_key = 'arman_akhtar_secret_key_123'

WHOLESALE_API_URL = "https://justanotherpanel.com/api/v2"
API_KEY = "f228184f39ac8288b61d24649df0606e"

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    # Users Table for Login/Signup
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            email TEXT UNIQUE,
            password TEXT,
            balance REAL DEFAULT 0.00
        )
    ''')
    # Orders Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            platform TEXT,
            service_type TEXT,
            link TEXT,
            quantity INTEGER,
            status TEXT
        )
    ''')
    # Tickets Table
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

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    user_id = session['user_id']
    cursor.execute('SELECT username, balance FROM users WHERE id = ?', (user_id,))
    user_row = cursor.fetchone()
    
    cursor.execute('SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC', (user_id,))
    orders = cursor.fetchall()
    
    cursor.execute('SELECT * FROM tickets WHERE user_id = ? ORDER BY id DESC', (user_id,))
    tickets = cursor.fetchall()
    
    conn.close()
    
    user_data = {
        "username": user_row[0] if user_row else "Arman Akhtar",
        "balance": f"Rs. {user_row[1]:,.2f}" if user_row else "Rs. 0.00",
        "raw_balance": user_row[1] if user_row else 0.00,
        "total_orders": len(orders)
    }
    
    return render_template('index.html', orders=orders, tickets=tickets, user=user_data)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, username FROM users WHERE email = ? AND password = ?', (email, password))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            return redirect(url_for('index'))
        else:
            error = "Ghalat Email ya Password! Dubara koshish karein."
            
    return render_template('login.html', error=error)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO users (username, email, password, balance) VALUES (?, ?, ?, ?)', 
                           (username, email, password, 0.00))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            error = "Yeh Email pehle se registered hai!"
            conn.close()
            
    return render_template('signup.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/google_login')
def google_login():
    # Demo Google Login simulation for Arman Akhtar
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE email = ?', ('arman.akhtar@gmail.com',))
    user = cursor.fetchone()
    
    if not user:
        cursor.execute('INSERT INTO users (username, email, password, balance) VALUES (?, ?, ?, ?)', 
                       ('Arman Akhtar', 'arman.akhtar@gmail.com', 'google_auth', 0.00))
        conn.commit()
        cursor.execute('SELECT id FROM users WHERE email = ?', ('arman.akhtar@gmail.com',))
        user = cursor.fetchone()
        
    session['user_id'] = user[0]
    session['username'] = 'Arman Akhtar'
    conn.close()
    return redirect(url_for('index'))

@app.route('/add_order', methods=['POST'])
def add_order():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    platform = request.form['platform']
    service_type = request.form['service_type']
    link = request.form['link']
    quantity = int(request.form['quantity'])
    user_id = session['user_id']
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT balance FROM users WHERE id = ?', (user_id,))
    current_balance = cursor.fetchone()[0]
    
    estimated_cost = quantity * 0.5
    
    if current_balance < estimated_cost:
        status_msg = "Error: Not enough funds on balance. Please add funds!"
    else:
        payload = {
            'key': API_KEY,
            'action': 'add',
            'service': 123,
            'link': link,
            'quantity': quantity
        }
        try:
            response = requests.post(WHOLESALE_API_URL, data=payload)
            result = response.json()
            if 'order' in result:
                status_msg = f"Sent to API (ID: {result['order']})"
                new_balance = current_balance - estimated_cost
                cursor.execute('UPDATE users SET balance = ? WHERE id = ?', (new_balance, user_id))
            else:
                status_msg = f"API Error: {result.get('error', 'Unknown')}"
        except Exception:
            status_msg = "Connection Failed"

    cursor.execute('INSERT INTO orders (user_id, platform, service_type, link, quantity, status) VALUES (?, ?, ?, ?, ?, ?)',
                   (user_id, platform, service_type, link, quantity, status_msg))
    conn.commit()
    conn.close()

    return redirect(url_for('index'))

@app.route('/mass_order', methods=['POST'])
def mass_order():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    links_data = request.form['mass_links']
    user_id = session['user_id']
    lines = links_data.split('\n')
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    for line in lines:
        if '|' in line:
            parts = line.split('|')
            link = parts[0].strip()
            qty = int(parts[1].strip()) if len(parts) > 1 and parts[1].strip().isdigit() else 100
            cursor.execute('INSERT INTO orders (user_id, platform, service_type, link, quantity, status) VALUES (?, ?, ?, ?, ?, ?)',
                           (user_id, 'Mass Order', 'Bulk Service', link, qty, 'Processing Mass Order'))
                           
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/add_funds', methods=['POST'])
def add_funds():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    amount = float(request.form['amount'])
    tid = request.form['tid']
    user_id = session['user_id']
    
    if amount > 0 and len(tid) >= 5:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT balance FROM users WHERE id = ?', (user_id,))
        current_balance = cursor.fetchone()[0]
        
        new_balance = current_balance + amount
        cursor.execute('UPDATE users SET balance = ? WHERE id = ?', (new_balance, user_id))
        conn.commit()
        conn.close()
        
    return redirect(url_for('index'))

@app.route('/create_ticket', methods=['POST'])
def create_ticket():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    subject = request.form['subject']
    message = request.form['message']
    user_id = session['user_id']
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO tickets (user_id, subject, message, status) VALUES (?, ?, ?, ?)',
                   (user_id, subject, message, 'Open'))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/get_services')
def get_services():
    payload = {
        'key': API_KEY,
        'action': 'services'
    }
    response = requests.post(WHOLESALE_API_URL, data=payload)
    return response.json()

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)