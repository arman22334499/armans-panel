import os
from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'smm_panel_super_secret_key_change_this'

# Database configuration (SQLite)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///smm_panel.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# User Database Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    balance = db.Column(db.Float, default=0.0)

# Create database tables automatically
with app.app_context():
    db.create_all()

# HTML Templates embedded securely to avoid missing template folder issues
HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SMM Panel - Next Wear</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body { background-color: #121212; color: #e0e0e0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        .navbar { background-color: #1f1f1f; border-bottom: 1px solid #333; }
        .card { background-color: #1e1e1e; border: 1px solid #333; color: #fff; }
        .form-control, .form-select { background-color: #2c2c2c; border: 1px solid #444; color: #fff; }
        .form-control:focus, .form-select:focus { background-color: #2c2c2c; border-color: #0d6efd; color: #fff; box-shadow: none; }
        .btn-primary { background-color: #0d6efd; border: none; }
        a { color: #0d6efd; text-decoration: none; }
        a:hover { color: #3d8bfd; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark px-4">
        <a class="navbar-brand fw-bold" href="/"><i class="fa-solid fa-bolt text-warning"></i> SMM Panel</a>
        <div class="ms-auto">
            {% if 'user_id' in session %}
                <span class="text-light me-3"><i class="fa-solid fa-wallet text-success"></i> Balance: ${{ "%.2f"|format(session.get('balance', 0.0)) }}</span>
                <a href="/dashboard" class="btn btn-sm btn-outline-light me-2">Dashboard</a>
                <a href="/logout" class="btn btn-sm btn-danger">Logout</a>
            {% else %}
                <a href="/login" class="btn btn-sm btn-outline-light me-2">Login</a>
                <a href="/register" class="btn btn-sm btn-primary">Register</a>
            {% endif %}
        </div>
    </nav>

    <div class="container mt-4">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ 'danger' if category == 'error' else 'success' }} alert-dismissible fade show" role="alert">
                        {{ message }}
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        {% block content %}{% endblock %}
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

INDEX_HTML = HTML_LAYOUT.replace('{% block content %}{% endblock %}', """
<div class="row justify-content-center mt-5">
    <div class="col-md-8 text-center">
        <h1 class="display-4 fw-bold mb-3">Best & Cheapest SMM Panel</h1>
        <p class="lead text-secondary mb-4">Boost your social media presence instantly with our automated services.</p>
        {% if 'user_id' not in session %}
            <a href="/register" class="btn btn-primary btn-lg px-4 me-2">Get Started</a>
            <a href="/login" class="btn btn-outline-light btn-lg px-4">Login</a>
        {% else %}
            <a href="/dashboard" class="btn btn-success btn-lg px-4">Go to Dashboard</a>
        {% endif %}
    </div>
</div>
""")

LOGIN_HTML = HTML_LAYOUT.replace('{% block content %}{% endblock %}', """
<div class="row justify-content-center mt-5">
    <div class="col-md-5">
        <div class="card p-4 shadow-sm">
            <h3 class="text-center mb-4">Login to Your Account</h3>
            <form method="POST">
                <div class="mb-3">
                    <label class="form-label">Username or Email</label>
                    <input type="text" name="username_or_email" class="form-control" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">Password</label>
                    <input type="password" name="password" class="form-control" required>
                </div>
                <button type="submit" class="btn btn-primary w-100 py-2">Login</button>
            </form>
            <div class="text-center mt-3">
                <small class="text-secondary">Don't have an account? <a href="/register">Register here</a></small>
            </div>
        </div>
    </div>
</div>
""")

REGISTER_HTML = HTML_LAYOUT.replace('{% block content %}{% endblock %}', """
<div class="row justify-content-center mt-4">
    <div class="col-md-5">
        <div class="card p-4 shadow-sm">
            <h3 class="text-center mb-4">Create an Account</h3>
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
                <button type="submit" class="btn btn-primary w-100 py-2">Register</button>
            </form>
            <div class="text-center mt-3">
                <small class="text-secondary">Already have an account? <a href="/login">Login here</a></small>
            </div>
        </div>
    </div>
</div>
""")

DASHBOARD_HTML = HTML_LAYOUT.replace('{% block content %}{% endblock %}', """
<div class="row mt-4">
    <div class="col-md-12">
        <div class="card p-4 mb-4">
            <h2>Welcome back, <span class="text-primary">{{ username }}</span>!</h2>
            <p class="text-secondary mb-0">Manage your orders and scale your social media effortlessly.</p>
        </div>
    </div>
    <div class="col-md-6">
        <div class="card p-4">
            <h4 class="mb-3"><i class="fa-solid fa-cart-plus text-primary"></i> New Order</h4>
            <form method="POST">
                <div class="mb-3">
                    <label class="form-label">Service Category</label>
                    <select class="form-select">
                        <option>Instagram Followers (HQ)</option>
                        <option>Instagram Likes</option>
                        <option>TikTok Views & Likes</option>
                        <option>YouTube Subscribers</option>
                    </select>
                </div>
                <div class="mb-3">
                    <label class="form-label">Target Link</label>
                    <input type="url" class="form-control" placeholder="https://..." required>
                </div>
                <div class="mb-3">
                    <label class="form-label">Quantity</label>
                    <input type="number" class="form-control" value="1000" min="100" required>
                </div>
                <button type="submit" class="btn btn-primary w-100">Submit Order</button>
            </form>
        </div>
    </div>
    <div class="col-md-6">
        <div class="card p-4 h-100">
            <h4 class="mb-3"><i class="fa-solid fa-chart-line text-success"></i> Quick Stats</h4>
            <ul class="list-group list-group-flush bg-transparent">
                <li class="list-group-item bg-transparent text-light d-flex justify-content-between align-items-center">
                    Total Orders <span class="badge bg-primary rounded-pill">0</span>
                </li>
                <li class="list-group-item bg-transparent text-light d-flex justify-content-between align-items-center">
                    Account Balance <span class="text-success fw-bold">${{ "%.2f"|format(balance) }}</span>
                </li>
            </ul>
        </div>
    </div>
</div>
""")

@app.route('/')
def index():
    return render_template_string(INDEX_HTML)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        email = request.form.get('email').strip().lower()
        password = request.form.get('password')

        # Check if user already exists
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Username or Email already exists! Please login.', 'error')
            return redirect(url_for('login'))

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_password, balance=0.0)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'error')

    return render_template_string(REGISTER_HTML)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form.get('username_or_email').strip()
        password = request.form.get('password')

        # Allow login via either username or email
        user = User.query.filter((User.username == identifier) | (User.email == identifier.lower())).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['balance'] = user.balance
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username/email or password!', 'error')

    return render_template_string(LOGIN_HTML)

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        flash('Please login to access the dashboard.', 'error')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('login'))

    if request.method == 'POST':
        flash('Order placed successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template_string(DASHBOARD_HTML, username=user.username, balance=user.balance)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
