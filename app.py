import os
from flask import Flask, render_template_string, request, redirect, url_for, flash, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'arman_panel_secret_key_123'

SERVICES_LIST = [
    {"id": 1, "name": "Instagram Followers [HQ & Non-Drop]", "category": "Instagram", "rate": 1.50, "min": 10, "max": 50000},
    {"id": 2, "name": "Instagram Likes [Instant]", "category": "Instagram", "rate": 0.50, "min": 50, "max": 100000},
    {"id": 3, "name": "Instagram Views [Reels/Video]", "category": "Instagram", "rate": 0.20, "min": 100, "max": 1000000},
    {"id": 4, "name": "TikTok Views [Super Fast]", "category": "TikTok", "rate": 0.10, "min": 100, "max": 5000000},
    {"id": 5, "name": "TikTok Followers [Real Look]", "category": "TikTok", "rate": 2.80, "min": 50, "max": 20000},
    {"id": 6, "name": "YouTube Subscribers [Lifetime Guarantee]", "category": "YouTube", "rate": 12.00, "min": 50, "max": 5000},
    {"id": 7, "name": "YouTube Monetization Watchtime", "category": "YouTube", "rate": 25.00, "min": 500, "max": 4000},
    {"id": 8, "name": "Facebook Page Likes & Followers", "category": "Facebook", "rate": 3.50, "min": 100, "max": 10000}
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
                balance REAL DEFAULT 10.00
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
    except Exception as e:
        print("Database Init Error:", e)

init_db()

def render_page(active_tab, title, inner_html):
    username = session.get('username', 'User')
    
    # Get balance safely
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM users WHERE id = ?", (session.get('user_id'),))
        row = cursor.fetchone()
        conn.close()
        balance = row['balance'] if row else 0.0
    except:
        balance = 0.0

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title} - Arman's Panel</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {{ background-color: #f4f7f6; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
            .sidebar {{ background: #1a1d20; min-height: 100vh; color: white; padding: 20px; box-shadow: 2px 0 5px rgba(0,0,0,0.1); }}
            .sidebar h4 {{ font-weight: 700; color: #0d6efd; }}
            .sidebar a {{ color: #adb5bd; text-decoration: none; display: block; padding: 12px 15px; border-radius: 8px; margin-bottom: 8px; font-weight: 500; transition: 0.3s; }}
            .sidebar a:hover, .sidebar a.active {{ background: #0d6efd; color: white; }}
            .card {{ border: none; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); background: white; }}
        </style>
    </head>
    <body>
        <div class="container-fluid">
            <div class="row">
                <div class="col-md-3 sidebar p-3">
                    <h4 class="mb-4 text-center">👑 Arman's Panel</h4>
                    <a href="/dashboard" class="{'active' if active_tab=='dashboard' else ''}">➕ New Order</a>
                    <a href="/services" class="{'active' if active_tab=='services' else ''}">📋 Services List</a>
                    <a href="/orders" class="{'active' if active_tab=='orders' else ''}">📦 Order History</a>
                    <a href="/add-funds" class="{'active' if active_tab=='add_funds' else ''}">💳 Add Funds</a>
                    <a href="/mass-order" class="{'active' if active_tab=='mass_order' else ''}">⚡ Mass Order</a>
                    <a href="/support-tickets" class="{'active' if active_tab=='support' else ''}">🎫 Support Tickets</a>
                    <hr class="text-secondary my-4">
                    <a href="/logout" class="text-danger fw-bold">🚪 Logout</a>
                </div>
                <div class="col-md-9 p-4">
                    <div class="d-flex justify-content-between align-items-center mb-4 bg-white p-3 rounded shadow-sm">
                        <h5 class="m-0">Welcome, <b class="text-primary">{username}</b></h5>
                        <span class="badge bg-success fs-6 px-3 py-2">Balance: ${balance:.2f}</span>
                    </div>
                    {inner_html}
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error_msg = ""
    if request.method == 'POST':
        login_input = request.form.get('email')
        password = request.form.get('password')

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
            error_msg = '<div class="alert alert-danger py-2">Ghalat Email/Username ya Password!</div>'

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Login - Arman's Panel</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="bg-light">
        <div class="container d-flex justify-content-center align-items-center vh-100">
            <div class="card p-4 shadow-lg" style="width: 420px;">
                <div class="text-center mb-4">
                    <h3 class="fw-bold text-primary">👑 Arman's Panel</h3>
                    <p class="text-muted">Sign in to your account</p>
                </div>
                {error_msg}
                <form method="POST">
                    <div class="mb-3">
                        <label class="form-label">Email ya Username</label>
                        <input type="text" name="email" class="form-control" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Password</label>
                        <input type="password" name="password" class="form-control" required>
                    </div>
                    <button type="submit" class="btn btn-primary w-100 py-2 fw-bold">Sign In</button>
                </form>
                <div class="text-center mt-3">
                    <a href="/signup" class="text-decoration-none">Account nahi hai? Sign Up karein</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    msg = ""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not username or not email or not password:
            msg = '<div class="alert alert-danger py-2">Tamam fields bharna lazmi hain!</div>'
        else:
            hashed_password = generate_password_hash(password)
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO users (username, email, password, balance) VALUES (?, ?, ?, ?)", 
                               (username, email, hashed_password, 10.00))
                conn.commit()
                conn.close()
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                msg = '<div class="alert alert-danger py-2">Yeh Email ya Username pehle se mojood hai!</div>'

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Sign Up - Arman's Panel</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="bg-light">
        <div class="container d-flex justify-content-center align-items-center vh-100">
            <div class="card p-4 shadow-lg" style="width: 420px;">
                <div class="text-center mb-4">
                    <h3 class="fw-bold text-success">📝 Create Account</h3>
                    <p class="text-muted">Get $10 free bonus on signup</p>
                </div>
                {msg}
                <form method="POST">
                    <div class="mb-3">
                        <label class="form-label">Username</label>
                        <input type="text" name="username" class="form-control" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Email Address</label>
                        <input type="email" name="email" class="form-control" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Password</label>
                        <input type="password" name="password" class="form-control" required>
                    </div>
                    <button type="submit" class="btn btn-success w-100 py-2 fw-bold">Sign Up</button>
                </form>
                <div class="text-center mt-3">
                    <a href="/login" class="text-decoration-none">Pehle se account hai? Login karein</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    alert_box = ""
    if request.method == 'POST':
        service_id = request.form.get('service_id')
        link = request.form.get('link')
        quantity_str = request.form.get('quantity')
        
        if service_id and link and quantity_str:
            try:
                quantity = int(quantity_str)
                selected_service = next((s for s in SERVICES_LIST if s['id'] == int(service_id)), None)
                
                if selected_service:
                    total_price = (quantity * selected_service['rate']) / 1000.0
                    
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT balance FROM users WHERE id = ?", (session['user_id'],))
                    current_balance = cursor.fetchone()['balance']
                    
                    if current_balance >= total_price:
                        cursor.execute("UPDATE users SET balance = balance - ? WHERE id = ?", (total_price, session['user_id']))
                        cursor.execute("INSERT INTO orders (user_id, service, link, quantity, price, status) VALUES (?, ?, ?, ?, ?, ?)",
                                       (session['user_id'], selected_service['name'], link, quantity, total_price, 'In Progress'))
                        conn.commit()
                        conn.close()
                        alert_box = f'<div class="alert alert-success">Order kamyaabi se place ho gaya! Cost: ${total_price:.2f}</div>'
                    else:
                        conn.close()
                        alert_box = '<div class="alert alert-danger">Aapke account mein balance kam hai!</div>'
            except Exception as e:
                alert_box = f'<div class="alert alert-danger">Error: {str(e)}</div>'

    options_html = ""
    for s in SERVICES_LIST:
        options_html += f"<option value='{s['id']}'>[{s['category']}] {s['name']} - ${s['rate']:.2f} per 1000</option>"

    content = f"""
    <div class="card p-4">
        <h4 class="mb-3 text-primary">Place New Order</h4>
        {alert_box}
        <form method="POST">
            <div class="mb-3">
                <label class="form-label fw-bold">Select Service</label>
                <select name="service_id" class="form-select" required>
                    {options_html}
                </select>
            </div>
            <div class="mb-3">
                <label class="form-label fw-bold">Target Link</label>
                <input type="url" name="link" class="form-control" placeholder="https://..." required>
            </div>
            <div class="mb-3">
                <label class="form-label fw-bold">Quantity</label>
                <input type="number" name="quantity" class="form-control" value="1000" min="10" required>
            </div>
            <button type="submit" class="btn btn-primary px-4 py-2 fw-bold">Place Order</button>
        </form>
    </div>
    """
    return render_page('dashboard', 'New Order', content)

@app.route('/services')
def services():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    rows = ""
    for s in SERVICES_LIST:
        rows += f"<tr><td><b>{s['id']}</b></td><td>{s['category']}</td><td>{s['name']}</td><td><b>${s['rate']:.2f}</b></td><td>{s['min']} / {s['max']}</td></tr>"

    content = f"""
    <div class="card p-4">
        <h4 class="mb-3 text-primary">Available SMM Services</h4>
        <table class="table table-hover align-middle mt-2">
            <thead><tr><th>ID</th><th>Category</th><th>Service Name</th><th>Rate per 1000</th><th>Min / Max</th></tr></thead>
            <tbody>{rows}</tbody>
        </table>
    </div>
    """
    return render_page('services', 'Services', content)

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
        
        rows = ""
        for o in orders_list:
            status_color = "bg-warning text-dark" if o['status'] == 'Pending' else "bg-success"
            rows += f"<tr><td>#{o['id']}</td><td>{o['service']}</td><td><a href='{o['link']}' target='_blank'>Link</a></td><td>{o['quantity']}</td><td><b>${o['price']:.2f}</b></td><td><span class='badge {status_color}'>{o['status']}</span></td></tr>"
    except Exception as e:
        rows = f"<tr><td colspan='6' class='text-center text-danger'>Error: {str(e)}</td></tr>"
    
    content = f"""
    <div class="card p-4">
        <h4 class="mb-3 text-primary">Order History</h4>
        <div class="table-responsive">
            <table class="table table-striped align-middle mt-2">
                <thead><tr><th>ID</th><th>Service</th><th>Link</th><th>Qty</th><th>Cost</th><th>Status</th></tr></thead>
                <tbody>{rows if rows else "<tr><td colspan='6' class='text-center text-muted'>Koi order nahi hai.</td></tr>"}</tbody>
            </table>
        </div>
    </div>
    """
    return render_page('orders', 'Order History', content)

@app.route('/add-funds')
def add_funds():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    content = """
    <div class="card p-4">
        <h4 class="mb-3 text-primary">Add Funds to Account</h4>
        <p class="text-muted">Funds add karne ke liye neech diye gaye methods par raabta karein:</p>
        <div class="row mt-4">
            <div class="col-md-6 mb-3">
                <div class="card border p-3 bg-light">
                    <h5 class="fw-bold text-dark">Easypaisa / JazzCash</h5>
                    <p class="mb-1">Account Title: <b>Arman Akhtar</b></p>
                    <p class="mb-0">Number: <b>0312-3456789</b></p>
                </div>
            </div>
            <div class="col-md-6 mb-3">
                <div class="card border p-3 bg-light">
                    <h5 class="fw-bold text-dark">Direct WhatsApp Support</h5>
                    <p class="mb-1">Payment screenshot WhatsApp par bhejein.</p>
                    <a href="https://wa.me/923001234567" target="_blank" class="btn btn-success btn-sm mt-2">Chat on WhatsApp</a>
                </div>
            </div>
        </div>
    </div>
    """
    return render_page('add_funds', 'Add Funds', content)

@app.route('/mass-order')
def mass_order():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    content = """
    <div class="card p-4">
        <h4 class="mb-3 text-primary">Mass Order</h4>
        <p class="text-muted">Har line mein aik order likhein: <code>service_id | link | quantity</code></p>
        <textarea class="form-control mb-3" rows="6" placeholder="1 | https://... | 1000"></textarea>
        <button class="btn btn-primary px-4">Submit Mass Orders</button>
    </div>
    """
    return render_page('mass_order', 'Mass Order', content)

@app.route('/support-tickets')
def support_tickets():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    content = """
    <div class="card p-4">
        <h4 class="mb-3 text-primary">Support Tickets</h4>
        <div class="mb-3">
            <label class="form-label fw-bold">Subject</label>
            <input type="text" class="form-control" placeholder="Masla kya hai?">
        </div>
        <div class="mb-3">
            <label class="form-label fw-bold">Message Details</label>
            <textarea class="form-control mb-3" rows="4" placeholder="Detail mein batayein..."></textarea>
        </div>
        <button class="btn btn-success px-4">Submit Ticket</button>
    </div>
    """
    return render_page('support', 'Support', content)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
