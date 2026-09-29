import os
from flask import Flask, render_template_string, request, redirect, url_for, flash, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'arman_panel_secret_key_123'

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
    except Exception as e:
        print("Database Init Error:", e)

init_db()

# Shared CSS Layout for all pages to look professional
BASE_LAYOUT = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Arman's Panel</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #f8f9fa; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        .sidebar { background: #212529; min-height: 100vh; color: white; padding: 20px; }
        .sidebar a { color: #cfd4da; text-decoration: none; display: block; padding: 10px 15px; border-radius: 5px; margin-bottom: 5px; }
        .sidebar a:hover, .sidebar a.active { background: #0d6efd; color: white; }
        .card { border: none; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    </style>
</head>
<body>
    {% block content %}{% endblock %}
</body>
</html>
'''

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
            
    html = BASE_LAYOUT.replace('{% block content %}{% endblock %}', '''
    <div class="container d-flex justify-content-center align-items-center vh-100">
        <div class="card p-4" style="width: 400px;">
            <h3 class="text-center mb-3">👑 Arman's Panel</h3>
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ category }}">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            <form method="POST">
                <div class="mb-3">
                    <label>Email ya Username</label>
                    <input type="text" name="email" class="form-control" required>
                </div>
                <div class="mb-3">
                    <label>Password</label>
                    <input type="password" name="password" class="form-control" required>
                </div>
                <button type="submit" class="btn btn-primary w-100">Sign In</button>
            </form>
            <div class="text-center mt-3">
                <a href="/signup">Account nahi hai? Sign Up karein</a>
            </div>
        </div>
    </div>
    ''')
    return render_template_string(html)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not username or not email or not password:
            flash('Tamam fields bharna lazmi hain!', 'danger')
            return redirect(url_for('signup'))

        hashed_password = generate_password_hash(password)

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", 
                           (username, email, hashed_password))
            conn.commit()
            conn.close()
            flash('Account kamyaabi se ban gaya! Ab login karein.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Yeh Email ya Username pehle se mojood hai!', 'danger')

    html = BASE_LAYOUT.replace('{% block content %}{% endblock %}', '''
    <div class="container d-flex justify-content-center align-items-center vh-100">
        <div class="card p-4" style="width: 400px;">
            <h3 class="text-center mb-3">📝 Create Account</h3>
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ category }}">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            <form method="POST">
                <div class="mb-3">
                    <label>Username</label>
                    <input type="text" name="username" class="form-control" required>
                </div>
                <div class="mb-3">
                    <label>Email Address</label>
                    <input type="email" name="email" class="form-control" required>
                </div>
                <div class="mb-3">
                    <label>Password</label>
                    <input type="password" name="password" class="form-control" required>
                </div>
                <button type="submit" class="btn btn-success w-100">Sign Up</button>
            </form>
            <div class="text-center mt-3">
                <a href="/login">Pehle se account hai? Login karein</a>
            </div>
        </div>
    </div>
    ''')
    return render_template_string(html)

def dashboard_layout(active_page, content):
    return BASE_LAYOUT.replace('{% block content %}{% endblock %}', f'''
    <div class="container-fluid">
        <div class="row">
            <div class="col-md-3 sidebar">
                <h4 class="text-white mb-4">👑 Arman's Panel</h4>
                <a href="/dashboard" class="{'active' if active_page=='new_order' else ''}">➕ New Order</a>
                <a href="/services" class="{'active' if active_page=='services' else ''}">📋 Services</a>
                <a href="/orders" class="{'active' if active_page=='orders' else ''}">📦 Orders</a>
                <a href="/add-funds" class="{'active' if active_page=='add_funds' else ''}">💳 Add Funds</a>
                <a href="/mass-order" class="{'active' if active_page=='mass_order' else ''}">⚡ Mass Order</a>
                <a href="/support-tickets" class="{'active' if active_page=='support' else ''}">🎫 Support</a>
                <hr class="text-secondary">
                <a href="/logout" class="text-danger">🚪 Logout</a>
            </div>
            <div class="col-md-9 p-4">
                <div class="d-flex justify-content-between align-items-center mb-4 bg-white p-3 rounded shadow-sm">
                    <h5>Welcome, <b>{session.get('username')}</b></h5>
                    <span class="badge bg-success fs-6">Balance: ${{ "{:.2f}".format(balance if 'balance' in locals() else 0.0) }}</span>
                </div>
                {content}
            </div>
        </div>
    </div>
    ''')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE id = ?", (session['user_id'],))
    user_data = cursor.fetchone()
    balance = user_data['balance'] if user_data else 0.0
    
    if request.method == 'POST':
        service = request.form.get('service')
        link = request.form.get('link')
        quantity = request.form.get('quantity')
        if service and link and quantity:
            cursor.execute("INSERT INTO orders (user_id, service, link, quantity, price) VALUES (?, ?, ?, ?, ?)",
                           (session['user_id'], service, link, int(quantity), 0.50))
            conn.commit()
            flash('Order kamyaabi se place ho gaya!', 'success')
            return redirect(url_for('dashboard'))
            
    conn.close()
    
    content = '''
    <div class="card p-4">
        <h4>New Order</h4>
        <form method="POST">
            <div class="mb-3">
                <label>Service Category</label>
                <select name="service" class="form-control">
                    <option value="Instagram Followers">Instagram Followers (HQ)</option>
                    <option value="TikTok Views">TikTok Views (Fast)</option>
                    <option value="YouTube Subscribers">YouTube Subscribers</option>
                </select>
            </div>
            <div class="mb-3">
                <label>Link</label>
                <input type="url" name="link" class="form-control" placeholder="https://..." required>
            </div>
            <div class="mb-3">
                <label>Quantity</label>
                <input type="number" name="quantity" class="form-control" value="1000" required>
            </div>
            <button type="submit" class="btn btn-primary">Place Order</button>
        </form>
    </div>
    '''
    return dashboard_layout('new_order', content)

@app.route('/services')
def services():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    content = '''
    <div class="card p-4">
        <h4>Available Services</h4>
        <table class="table table-striped mt-3">
            <thead><tr><th>ID</th><th>Service Name</th><th>Rate per 1000</th></tr></thead>
            <tbody>
                <tr><td>1</td><td>Instagram Followers (HQ)</td><td>$1.50</td></tr>
                <tr><td>2</td><td>TikTok Views (Fast)</td><td>$0.20</td></tr>
                <tr><td>3</td><td>YouTube Subscribers</td><td>$5.00</td></tr>
            </tbody>
        </table>
    </div>
    '''
    return dashboard_layout('services', content)

@app.route('/orders')
def orders():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, service, link, quantity, price, status FROM orders WHERE user_id = ?", (session['user_id'],))
    orders_list = cursor.fetchall()
    conn.close()
    
    rows = ""
    for o in orders_list:
        rows += f"<tr><td>{o['id']}</td><td>{o['service']}</td><td>{o['link']}</td><td>{o['quantity']}</td><td><span class='badge bg-warning'>{o['status']}</span></td></tr>"
    
    content = f'''
    <div class="card p-4">
        <h4>Order History</h4>
        <table class="table mt-3">
            <thead><tr><th>ID</th><th>Service</th><th>Link</th><th>Qty</th><th>Status</th></tr></thead>
            <tbody>{rows if rows else "<tr><td colspan='5' class='text-center'>Koi order nahi hai</td></tr>"}</tbody>
        </table>
    </div>
    '''
    return dashboard_layout('orders', content)

@app.route('/add-funds')
def add_funds():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    content = '''
    <div class="card p-4">
        <h4>Add Funds</h4>
        <p class="text-muted">Apne account mein funds add karne ke liye admin se rabta karein.</p>
        <div class="alert alert-info">WhatsApp Support: +92 3XXXXXXXXX</div>
    </div>
    '''
    return dashboard_layout('add_funds', content)

@app.route('/mass-order')
def mass_order():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    content = '''
    <div class="card p-4">
        <h4>Mass Order</h4>
        <textarea class="form-control mb-3" rows="5" placeholder="service_id | link | quantity"></textarea>
        <button class="btn btn-primary">Submit Mass Order</button>
    </div>
    '''
    return dashboard_layout('mass_order', content)

@app.route('/support-tickets')
def support_tickets():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    content = '''
    <div class="card p-4">
        <h4>Support Tickets</h4>
        <textarea class="form-control mb-3" rows="3" placeholder="Apna masla yahan likhein..."></textarea>
        <button class="btn btn-success">Send Ticket</button>
    </div>
    '''
    return dashboard_layout('support', content)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
