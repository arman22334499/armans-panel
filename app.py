import os
from flask import Flask, render_template_string, request, redirect, url_for, flash, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'arman_panel_secure_key_999'

# Services with Rates in PKR
SERVICES_LIST = [
    {"id": 1, "name": "📸 Instagram Followers [HQ & Non-Drop]", "category": "Instagram", "rate": 450, "min": 10, "max": 50000},
    {"id": 2, "name": "📸 Instagram Likes [Instant Delivery]", "category": "Instagram", "rate": 150, "min": 50, "max": 100000},
    {"id": 3, "name": "📸 Instagram Views [Reels / Video]", "category": "Instagram", "rate": 50, "min": 100, "max": 1000000},
    {"id": 4, "name": "🎵 TikTok Views [Super Fast]", "category": "TikTok", "rate": 30, "min": 100, "max": 5000000},
    {"id": 5, "name": "🎵 TikTok Followers [Real Looking]", "category": "TikTok", "rate": 850, "min": 50, "max": 20000},
    {"id": 6, "name": "📺 YouTube Subscribers [Lifetime Guarantee]", "category": "YouTube", "rate": 3500, "min": 50, "max": 5000},
    {"id": 7, "name": "📺 YouTube Monetization Watchtime Hours", "category": "YouTube", "rate": 7000, "min": 500, "max": 4000},
    {"id": 8, "name": "📘 Facebook Page Likes & Followers", "category": "Facebook", "rate": 1100, "min": 100, "max": 10000}
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
                balance REAL DEFAULT 5000.00
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
        print("DB Init Error:", e)

init_db()

def get_user_balance(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        return row['balance'] if row else 0.0
    except:
        return 0.0

# Master Layout Template (Professional SMM Dashboard Theme)
MASTER_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} - Arman's SMM Panel</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body { background-color: #f8f9fa; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        .sidebar { background: #121619; min-height: 100vh; color: white; padding: 20px; box-shadow: 3px 0 10px rgba(0,0,0,0.1); }
        .sidebar h4 { font-weight: 800; color: #0d6efd; letter-spacing: 0.5px; }
        .sidebar a { color: #a0aec0; text-decoration: none; display: block; padding: 12px 16px; border-radius: 8px; margin-bottom: 8px; font-weight: 500; transition: all 0.2s ease-in-out; }
        .sidebar a:hover, .sidebar a.active { background: #0d6efd; color: white; transform: translateX(4px); }
        .card { border: none; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.04); background: white; }
        .top-navbar { background: white; border-radius: 12px; padding: 15px 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.03); }
    </style>
</head>
<body>
    <div class="container-fluid">
        <div class="row">
            <!-- Sidebar -->
            <div class="col-md-3 col-lg-2 sidebar p-3 d-none d-md-block">
                <div class="text-center mb-4 mt-2">
                    <h4>👑 Arman Panel</h4>
                </div>
                <a href="/dashboard" class="{% if active_tab == 'dashboard' %}active{% endif %}"><i class="fas fa-cart-plus me-2"></i> New Order</a>
                <a href="/services" class="{% if active_tab == 'services' %}active{% endif %}"><i class="fas fa-list-ul me-2"></i> Services List</a>
                <a href="/orders" class="{% if active_tab == 'orders' %}active{% endif %}"><i class="fas fa-box-open me-2"></i> Order History</a>
                <a href="/add-funds" class="{% if active_tab == 'add_funds' %}active{% endif %}"><i class="fas fa-wallet me-2"></i> Add Funds</a>
                <a href="/mass-order" class="{% if active_tab == 'mass_order' %}active{% endif %}"><i class="fas fa-bolt me-2"></i> Mass Order</a>
                <a href="/support-tickets" class="{% if active_tab == 'support' %}active{% endif %}"><i class="fas fa-headset me-2"></i> Support Tickets</a>
                <hr class="text-secondary my-4">
                <a href="/logout" class="text-danger fw-bold"><i class="fas fa-sign-out-alt me-2"></i> Logout</a>
            </div>

            <!-- Main Content Area -->
            <div class="col-md-9 col-lg-10 p-4">
                <div class="top-navbar d-flex justify-content-between align-items-center mb-4">
                    <h5 class="m-0 text-dark fw-bold">Welcome, <span class="text-primary">{{ username }}</span></h5>
                    <div class="d-flex align-items-center gap-3">
                        <span class="badge bg-success fs-6 px-3 py-2 shadow-sm"><i class="fas fa-wallet me-1"></i> Balance: Rs. {{ "%.2f"|format(balance) }}</span>
                    </div>
                </div>

                {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}
                        {% for category, message in messages %}
                            <div class="alert alert-{{ category }} alert-dismissible fade show" role="alert">
                                {{ message }}
                                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                            </div>
                        {% endfor %}
                    {% endif %}
                {% endwith %}

                {{ content | safe }}
            </div>
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
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

    auth_template = '''
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
                {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}
                        {% for category, message in messages %}
                            <div class="alert alert-{{ category }} py-2">{{ message }}</div>
                        {% endfor %}
                    {% endif %}
                {% endwith %}
                <form method="POST">
                    <div class="mb-3">
                        <label class="form-label fw-bold">Email ya Username</label>
                        <input type="text" name="email" class="form-control" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label fw-bold">Password</label>
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
    '''
    return render_template_string(auth_template)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not username or not email or not password:
            flash('Tamam fields bharna lazmi hain!', 'danger')
        else:
            hashed_password = generate_password_hash(password)
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO users (username, email, password, balance) VALUES (?, ?, ?, ?)", 
                               (username, email, hashed_password, 5000.00))
                conn.commit()
                conn.close()
                flash('Account kamyaabi se ban gaya! Free Rs. 5000 bonus add ho gaye hain, ab login karein.', 'success')
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                flash('Yeh Email ya Username pehle se mojood hai!', 'danger')

    signup_template = '''
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
                    <p class="text-muted">Get Rs. 5000 free bonus on signup</p>
                </div>
                {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}
                        {% for category, message in messages %}
                            <div class="alert alert-{{ category }} py-2">{{ message }}</div>
                        {% endfor %}
                    {% endif %}
                {% endwith %}
                <form method="POST">
                    <div class="mb-3">
                        <label class="form-label fw-bold">Username</label>
                        <input type="text" name="username" class="form-control" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label fw-bold">Email Address</label>
                        <input type="email" name="email" class="form-control" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label fw-bold">Password</label>
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
    '''
    return render_template_string(signup_template)

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
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
                    current_balance = get_user_balance(session['user_id'])
                    
                    if current_balance >= total_price:
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute("UPDATE users SET balance = balance - ? WHERE id = ?", (total_price, session['user_id']))
                        cursor.execute("INSERT INTO orders (user_id, service, link, quantity, price, status) VALUES (?, ?, ?, ?, ?, ?)",
                                       (session['user_id'], selected_service['name'], link, quantity, total_price, 'In Progress'))
                        conn.commit()
                        conn.close()
                        flash(f'Order kamyaabi se place ho gaya! Total cost: Rs. {total_price:.2f}', 'success')
                    else:
                        flash('Aapke account mein balance kam hai!', 'danger')
            except Exception as e:
                flash(f'Error: {str(e)}', 'danger')
            return redirect(url_for('dashboard'))

    content = '''
    <div class="card p-4">
        <h4 class="mb-3 text-primary fw-bold"><i class="fas fa-cart-plus me-2"></i> Place New Order</h4>
        <form method="POST">
            <div class="mb-3">
                <label class="form-label fw-bold">Select Service</label>
                <select name="service_id" id="serviceSelect" class="form-select" onchange="calculateTotal()" required>
                    {% for s in services %}
                    <option value="{{ s.id }}" data-rate="{{ s.rate }}">[{{ s.category }}] {{ s.name }} - Rs. {{ s.rate }} per 1000</option>
                    {% endfor %}
                </select>
            </div>
            <div class="mb-3">
                <label class="form-label fw-bold">Target Link</label>
                <input type="url" name="link" class="form-control" placeholder="https://..." required>
            </div>
            <div class="mb-3">
                <label class="form-label fw-bold">Quantity</label>
                <input type="number" name="quantity" id="quantityInput" class="form-control" value="1000" min="10" oninput="calculateTotal()" required>
            </div>
            <div class="mb-3 p-3 bg-light rounded border">
                <h6 class="m-0 text-secondary">Total Charge: <b class="text-success fs-5" id="totalCost">Rs. 0.00</b></h6>
            </div>
            <button type="submit" class="btn btn-primary px-4 py-2 fw-bold shadow-sm">Place Order</button>
        </form>
    </div>
    <script>
        function calculateTotal() {
            var select = document.getElementById('serviceSelect');
            var qty = document.getElementById('quantityInput').value;
            var selectedOption = select.options[select.selectedIndex];
            var rate = parseFloat(selectedOption.getAttribute('data-rate')) || 0;
            var total = (qty * rate) / 1000.0;
            document.getElementById('totalCost').innerText = 'Rs. ' + total.toFixed(2);
        }
        window.onload = calculateTotal;
    </script>
    '''
    rendered_content = render_template_string(content, services=SERVICES_LIST)
    return render_template_string(MASTER_TEMPLATE, active_tab='dashboard', title='New Order', username=session.get('username'), balance=get_user_balance(session.get('user_id')), content=rendered_content)

@app.route('/services')
def services():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    content = '''
    <div class="card p-4">
        <h4 class="mb-3 text-primary fw-bold"><i class="fas fa-list-ul me-2"></i> Available SMM Services</h4>
        <div class="table-responsive">
            <table class="table table-hover align-middle mt-2">
                <thead class="table-light">
                    <tr><th>ID</th><th>Category</th><th>Service Name</th><th>Rate per 1000 (PKR)</th><th>Min / Max</th></tr>
                </thead>
                <tbody>
                    {% for s in services %}
                    <tr>
                        <td><b>{{ s.id }}</b></td>
                        <td><span class="badge bg-secondary">{{ s.category }}</span></td>
                        <td>{{ s.name }}</td>
                        <td><b class="text-success">Rs. {{ s.rate }}</b></td>
                        <td>{{ s.min }} / {{ s.max }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    '''
    rendered_content = render_template_string(content, services=SERVICES_LIST)
    return render_template_string(MASTER_TEMPLATE, active_tab='services', title='Services List', username=session.get('username'), balance=get_user_balance(session.get('user_id')), content=rendered_content)

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

    content = '''
    <div class="card p-4">
        <h4 class="mb-3 text-primary fw-bold"><i class="fas fa-box-open me-2"></i> Order History</h4>
        <div class="table-responsive">
            <table class="table table-striped align-middle mt-2">
                <thead class="table-light">
                    <tr><th>ID</th><th>Service</th><th>Link</th><th>Qty</th><th>Cost</th><th>Status</th></tr>
                </thead>
                <tbody>
                    {% if orders %}
                        {% for o in orders %}
                        <tr>
                            <td>#{{ o.id }}</td>
                            <td>{{ o.service }}</td>
                            <td><a href="{{ o.link }}" target="_blank" class="text-decoration-none">Open Link</a></td>
                            <td>{{ o.quantity }}</td>
                            <td><b class="text-success">Rs. {{ "%.2f"|format(o.price) }}</b></td>
                            <td><span class="badge bg-warning text-dark">{{ o.status }}</span></td>
                        </tr>
                        {% endfor %}
                    {% else %}
                        <tr><td colspan="6" class="text-center text-muted py-4">Abhi tak koi order place nahi kiya gaya.</td></tr>
                    {% endif %}
                </tbody>
            </table>
        </div>
    </div>
    '''
    rendered_content = render_template_string(content, orders=orders_list)
    return render_template_string(MASTER_TEMPLATE, active_tab='orders', title='Order History', username=session.get('username'), balance=get_user_balance(session.get('user_id')), content=rendered_content)

@app.route('/add-funds')
def add_funds():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    content = '''
    <div class="card p-4">
        <h4 class="mb-3 text-primary fw-bold"><i class="fas fa-wallet me-2"></i> Add Funds to Account</h4>
        <p class="text-muted">Apne account mein balance add karne ke liye neech diye gaye payment methods par raqam transfer karein:</p>
        <div class="row mt-4">
            <div class="col-md-4 mb-3">
                <div class="card border p-3 bg-light h-100">
                    <h5 class="fw-bold text-success"><i class="fas fa-mobile-alt me-1"></i> Easypaisa</h5>
                    <p class="mb-1">Title: <b>Arman Akhtar</b></p>
                    <p class="mb-0">Number: <b>03281583582</b></p>
                </div>
            </div>
            <div class="col-md-4 mb-3">
                <div class="card border p-3 bg-light h-100">
                    <h5 class="fw-bold text-primary"><i class="fas fa-university me-1"></i> NayaPay</h5>
                    <p class="mb-1">Title: <b>Arman Akhtar</b></p>
                    <p class="mb-0">Number: <b>03281583582</b></p>
                </div>
            </div>
            <div class="col-md-4 mb-3">
                <div class="card border p-3 bg-light h-100">
                    <h5 class="fw-bold text-info"><i class="fas fa-credit-card me-1"></i> SadaPay</h5>
                    <p class="mb-1">Title: <b>Arman Akhtar</b></p>
                    <p class="mb-0">Number: <b>03281583582</b></p>
                </div>
            </div>
        </div>
        <div class="mt-4 p-3 bg-white border rounded">
            <h6 class="fw-bold">Payment ke baad kya karein?</h6>
            <p class="text-muted mb-2">Raqam transfer karne ke baad screenshot ya transaction ID hamare WhatsApp support par bhejein taaki foran balance add ho jaye.</p>
            <a href="https://wa.me/923281583582" target="_blank" class="btn btn-success fw-bold px-4"><i class="fab fa-whatsapp me-2"></i> Chat on WhatsApp</a>
        </div>
    </div>
    '''
    return render_template_string(MASTER_TEMPLATE, active_tab='add_funds', title='Add Funds', username=session.get('username'), balance=get_user_balance(session.get('user_id')), content=content)

@app.route('/mass-order')
def mass_order():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    content = '''
    <div class="card p-4">
        <h4 class="mb-3 text-primary fw-bold"><i class="fas fa-bolt me-2"></i> Mass Order</h4>
        <p class="text-muted">Har line mein aik order likhein is format mein: <code>service_id | link | quantity</code></p>
        <textarea class="form-control mb-3" rows="6" placeholder="1 | https://instagram.com/p/abc | 1000&#10;4 | https://tiktok.com/@user/video/123 | 5000"></textarea>
        <button class="btn btn-primary px-4 fw-bold">Submit Mass Orders</button>
    </div>
    '''
    return render_template_string(MASTER_TEMPLATE, active_tab='mass_order', title='Mass Order', username=session.get('username'), balance=get_user_balance(session.get('user_id')), content=content)

@app.route('/support-tickets')
def support_tickets():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    content = '''
    <div class="card p-4">
        <h4 class="mb-3 text-primary fw-bold"><i class="fas fa-headset me-2"></i> Support Tickets</h4>
        <div class="mb-3">
            <label class="form-label fw-bold">Subject / Masla</label>
            <input type="text" class="form-control" placeholder="Misal ke tor par: Order refill request">
        </div>
        <div class="mb-3">
            <label class="form-label fw-bold">Message Details</label>
            <textarea class="form-control mb-3" rows="4" placeholder="Apni detail yahan likhein..."></textarea>
        </div>
        <button class="btn btn-success px-4 fw-bold">Submit Ticket</button>
    </div>
    '''
    return render_template_string(MASTER_TEMPLATE, active_tab='support', title='Support Tickets', username=session.get('username'), balance=get_user_balance(session.get('user_id')), content=content)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
