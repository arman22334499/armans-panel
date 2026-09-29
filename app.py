import os
import requests
from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'arman_smm_panel_secure_key_2026'

SMM_API_URL = "https://supplier-smm-panel-url.com/api/v2" 
SMM_API_KEY = "YOUR_SUPPLIER_API_KEY_HERE"

INITIAL_SERVICES = [
    {"id": 4317, "api_service_id": 101, "name": "Hostinger Premium Plan | Domain + Hosting 1 Year Plan", "category": "🌐 Hostinger Domain + Hosting", "rate": 4999, "min": 1, "max": 1, "icon": "fas fa-globe"},
    {"id": 1, "api_service_id": 201, "name": "Instagram Followers [Low Drop] | Premium", "category": "📸 Instagram Followers", "rate": 450, "min": 10, "max": 20000, "icon": "fab fa-instagram"},
    {"id": 2, "api_service_id": 202, "name": "Instagram Followers [Real - Mix Data]", "category": "📸 Instagram Followers", "rate": 350, "min": 50, "max": 50000, "icon": "fab fa-instagram"},
    {"id": 3, "api_service_id": 203, "name": "Instagram Story Views [Instant]", "category": "📸 Instagram Story Views", "rate": 120, "min": 100, "max": 100000, "icon": "fas fa-eye"},
    {"id": 4, "api_service_id": 204, "name": "Instagram Poll Reactions [Real Votes]", "category": "📸 Instagram Poll Reactions", "rate": 200, "min": 50, "max": 10000, "icon": "fas fa-poll"},
    {"id": 5, "api_service_id": 205, "name": "Instagram Likes [Super Fast]", "category": "📸 Instagram Likes", "rate": 150, "min": 50, "max": 50000, "icon": "fas fa-heart"},
    {"id": 6, "api_service_id": 301, "name": "TikTok Views [Super Fast & Cheap]", "category": "🎵 TikTok Views", "rate": 30, "min": 100, "max": 5000000, "icon": "fab fa-tiktok"},
    {"id": 7, "api_service_id": 302, "name": "TikTok Followers [Real Looking]", "category": "🎵 TikTok Followers", "rate": 850, "min": 50, "max": 20000, "icon": "fab fa-tiktok"},
    {"id": 8, "api_service_id": 303, "name": "TikTok Video Likes [High Quality]", "category": "🎵 TikTok Video Likes", "rate": 250, "min": 50, "max": 50000, "icon": "fab fa-tiktok"},
    {"id": 9, "api_service_id": 304, "name": "TikTok Page / Profile Likes", "category": "🎵 TikTok Page Likes", "rate": 300, "min": 50, "max": 30000, "icon": "fab fa-tiktok"},
    {"id": 10, "api_service_id": 401, "name": "YouTube Subscribers [Lifetime Guarantee]", "category": "▶️ YouTube Subscribers", "rate": 3500, "min": 50, "max": 5000, "icon": "fab fa-youtube"},
    {"id": 11, "api_service_id": 402, "name": "YouTube Watchtime Hours [Monetization]", "category": "▶️ YouTube Watchtime", "rate": 7000, "min": 500, "max": 4000, "icon": "fas fa-clock"},
    {"id": 12, "api_service_id": 403, "name": "YouTube Video Likes [Instant]", "category": "▶️ YouTube Likes", "rate": 400, "min": 50, "max": 10000, "icon": "fas fa-thumbs-up"},
    {"id": 13, "api_service_id": 501, "name": "Facebook Page Followers & Likes", "category": "📘 Facebook Page Followers", "rate": 1100, "min": 100, "max": 10000, "icon": "fab fa-facebook"},
    {"id": 14, "api_service_id": 502, "name": "Facebook Video Views [HQ]", "category": "📘 Facebook Video Views", "rate": 200, "min": 100, "max": 100000, "icon": "fas fa-video"},
    {"id": 15, "api_service_id": 601, "name": "WhatsApp Channel Followers", "category": "💚 WhatsApp Channel Followers", "rate": 1500, "min": 100, "max": 25000, "icon": "fab fa-whatsapp"}
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
                total_spent REAL DEFAULT 52.05,
                is_admin INTEGER DEFAULT 0
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
                status TEXT DEFAULT 'Pending',
                api_order_id TEXT DEFAULT NULL
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
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                gateway TEXT,
                amount REAL,
                transaction_id TEXT,
                status TEXT DEFAULT 'Completed'
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                api_service_id INTEGER,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                rate REAL NOT NULL,
                min INTEGER DEFAULT 10,
                max INTEGER DEFAULT 10000,
                icon TEXT DEFAULT 'fas fa-star'
            )
        ''')
        
        cursor.execute("SELECT COUNT(*) FROM services")
        if cursor.fetchone()[0] == 0:
            for s in INITIAL_SERVICES:
                cursor.execute("INSERT INTO services (id, api_service_id, name, category, rate, min, max, icon) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                               (s['id'], s['api_service_id'], s['name'], s['category'], s['rate'], s['min'], s['max'], s['icon']))

        cursor.execute("SELECT * FROM users WHERE username = 'admin'")
        if not cursor.fetchone():
            admin_pass = generate_password_hash('admin123')
            cursor.execute("INSERT INTO users (username, email, password, balance, total_spent, is_admin) VALUES (?, ?, ?, ?, ?, ?)",
                           ('admin', 'admin@armansmm.com', admin_pass, 5000.0, 0.0, 1))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print("DB Init Error:", e)

init_db()

def get_supplier_balance():
    try:
        payload = {'key': SMM_API_KEY, 'action': 'balance'}
        response = requests.post(SMM_API_URL, data=payload, timeout=5)
        res = response.json()
        if 'balance' in res:
            return f"{res['balance']} {res.get('currency', 'USD')}"
    except:
        pass
    return "N/A"

def get_all_services():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM services")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except:
        return INITIAL_SERVICES

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
        return redirect(url_for('admin_panel' if session.get('is_admin') == 1 else 'dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_input = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            # Support both username or email login
            cursor.execute("SELECT * FROM users WHERE email = ? OR username = ?", (login_input, login_input))
            user = cursor.fetchone()
            conn.close()

            if user and check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['is_admin'] = user['is_admin']
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
            existing_user = cursor.fetchone()
            
            if existing_user:
                flash('Yeh Email ya Username pehle se mojood hai!', 'danger')
                conn.close()
                return redirect(url_for('signup'))

            cursor.execute("INSERT INTO users (username, email, password, balance, total_spent, is_admin) VALUES (?, ?, ?, ?, ?, ?)", 
                           (username, email, hashed_password, 162.95, 52.05, 0))
            conn.commit()
            conn.close()
            flash('Account kamyabi se ban gaya! Ab aap login kar sakte hain.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            flash(f'Signup mein masla aaya hai: {str(e)}', 'danger')
            return redirect(url_for('signup'))
            
    return render_template('signup.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        new_password = request.form.get('new_password', '').strip()
        
        if email and new_password:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
                user = cursor.fetchone()
                if user:
                    hashed_pw = generate_password_hash(new_password)
                    cursor.execute("UPDATE users SET password = ? WHERE email = ?", (hashed_pw, email))
                    conn.commit()
                    conn.close()
                    flash('Password kamyabi se reset ho gaya! Ab aap naye password se login karein.', 'success')
                    return redirect(url_for('login'))
                else:
                    conn.close()
                    flash('Yeh email system mein mojood nahi hai!', 'danger')
            except Exception as e:
                flash(f'Error: {str(e)}', 'danger')
        else:
            flash('Tamam fields bharna lazmi hain!', 'danger')
    return render_template('forgot_password.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = get_user_data(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('login'))

    services_list = get_all_services()

    if request.method == 'POST':
        service_id = request.form.get('service_id')
        link = request.form.get('link')
        quantity_str = request.form.get('quantity')
        
        if service_id and link and quantity_str:
            try:
                quantity = int(quantity_str)
                selected_service = next((s for s in services_list if s['id'] == int(service_id)), None)
                if selected_service:
                    total_price = (quantity * selected_service['rate']) / 1000.0 if selected_service['min'] > 1 else selected_service['rate']
                    
                    if user['balance'] >= total_price:
                        api_order_id = None
                        order_status = 'Pending'
                        try:
                            payload = {
                                'key': SMM_API_KEY,
                                'action': 'add',
                                'service': selected_service['api_service_id'],
                                'link': link,
                                'quantity': quantity
                            }
                            response = requests.post(SMM_API_URL, data=payload, timeout=10)
                            res_json = response.json()
                            if 'order' in res_json:
                                api_order_id = str(res_json['order'])
                                order_status = 'In Progress'
                        except Exception as api_err:
                            print("API Connection Error:", api_err)

                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute("UPDATE users SET balance = balance - ?, total_spent = total_spent + ? WHERE id = ?", (total_price, total_price, session['user_id']))
                        cursor.execute("INSERT INTO orders (user_id, service, link, quantity, price, status, api_order_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                       (session['user_id'], f"[{selected_service['id']}] {selected_service['name']}", link, quantity, total_price, order_status, api_order_id))
                        conn.commit()
                        conn.close()
                        flash(f'Order successfully place ho gaya! Total: PKR Rs. {total_price:.2f}', 'success')
                    else:
                        flash('Aapke account mein balance kam hai!', 'danger')
            except Exception as e:
                flash(f'Error: {str(e)}', 'danger')
            return redirect(url_for('dashboard'))

    return render_template('dashboard.html', services=services_list, user=user)

@app.route('/bulk-order', methods=['GET', 'POST'])
def bulk_order():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = get_user_data(session['user_id'])
    
    if request.method == 'POST':
        bulk_text = request.form.get('bulk_text', '').strip()
        if bulk_text:
            lines = bulk_text.split('\n')
            success_count = 0
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                
                for line in lines:
                    parts = line.strip().split('|')
                    if len(parts) >= 3:
                        service_id, link, qty = parts[0].strip(), parts[1].strip(), parts[2].strip()
                        try:
                            cursor.execute("SELECT * FROM services WHERE id = ?", (service_id,))
                            srv = cursor.fetchone()
                            if srv and qty.isdigit():
                                quantity = int(qty)
                                price = (quantity * srv['rate']) / 1000.0 if srv['min'] > 1 else srv['rate']
                                
                                cursor.execute("SELECT balance FROM users WHERE id = ?", (session['user_id'],))
                                curr_bal = cursor.fetchone()['balance']
                                
                                if curr_bal >= price:
                                    cursor.execute("UPDATE users SET balance = balance - ?, total_spent = total_spent + ? WHERE id = ?", (price, price, session['user_id']))
                                    cursor.execute("INSERT INTO orders (user_id, service, link, quantity, price, status) VALUES (?, ?, ?, ?, ?, ?)",
                                                   (session['user_id'], f"[{srv['id']}] {srv['name']}", link, quantity, price, 'In Progress'))
                                    success_count += 1
                        except:
                            pass
                conn.commit()
                conn.close()
                flash(f'{success_count} orders bulk mein kamyabi se place ho gaye hain!', 'success')
            except Exception as e:
                flash(f'Bulk order error: {str(e)}', 'danger')
            return redirect(url_for('orders'))
            
    return render_template('bulk_order.html', user=user)

@app.route('/services')
def services():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = get_user_data(session['user_id'])
    return render_template('services.html', services=get_all_services(), user=user)

@app.route('/orders')
def orders():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, api_order_id FROM orders WHERE user_id = ? AND status != 'Completed' AND api_order_id IS NOT NULL", (session['user_id'],))
        pending_sync_orders = cursor.fetchall()
        
        for ord_row in pending_sync_orders:
            try:
                payload = {'key': SMM_API_KEY, 'action': 'status', 'order': ord_row['api_order_id']}
                resp = requests.post(SMM_API_URL, data=payload, timeout=3).json()
                if 'status' in resp:
                    new_st = resp['status'].capitalize()
                    cursor.execute("UPDATE orders SET status = ? WHERE id = ?", (new_st, ord_row['id']))
            except:
                pass
        conn.commit()
        
        cursor.execute("SELECT id, service, link, quantity, price, status FROM orders WHERE user_id = ? ORDER BY id DESC", (session['user_id'],))
        orders_list = cursor.fetchall()
        conn.close()
    except:
        orders_list = []
    user = get_user_data(session['user_id'])
    return render_template('orders.html', orders=orders_list, user=user)

@app.route('/addfunds', methods=['GET', 'POST'])
def add_funds():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        gateway = request.form.get('gateway')
        amount_str = request.form.get('amount')
        transaction_id = request.form.get('transaction_id')
        
        if amount_str and transaction_id:
            try:
                amount = float(amount_str)
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, session['user_id']))
                cursor.execute("INSERT INTO transactions (user_id, gateway, amount, transaction_id, status) VALUES (?, ?, ?, ?, ?)",
                               (session['user_id'], gateway, amount, transaction_id, 'Completed'))
                conn.commit()
                conn.close()
                flash(f'Rs. {amount:.2f} successfully aapke account mein add ho gaye hain!', 'success')
            except Exception as e:
                flash(f'Error adding funds: {str(e)}', 'danger')
        return redirect(url_for('add_funds'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, gateway, amount, transaction_id, status FROM transactions WHERE user_id = ? ORDER BY id DESC", (session['user_id'],))
        transactions = cursor.fetchall()
        conn.close()
    except:
        transactions = []

    user = get_user_data(session['user_id'])
    return render_template('add_funds.html', user=user, transactions=transactions)

@app.route('/support-tickets', methods=['GET', 'POST'])
def support_tickets():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()
        if subject and message:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO tickets (user_id, subject, message, status) VALUES (?, ?, ?, ?)",
                               (session['user_id'], subject, message, 'Open'))
                conn.commit()
                conn.close()
                flash('Ticket submit ho gayi!', 'success')
            except Exception as e:
                flash(f'Error: {str(e)}', 'danger')
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

@app.reset_db_route_if_needed = True # dummy placeholder comment

@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    if 'user_id' not in session or session.get('is_admin') != 1:
        flash('Access denied! Admin login required.', 'danger')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        category = request.form.get('category')
        rate = request.form.get('rate')
        api_service_id = request.form.get('api_service_id')
        
        if name and category and rate:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO services (api_service_id, name, category, rate, min, max, icon) VALUES (?, ?, ?, ?, ?, ?, ?)",
                               (int(api_service_id or 100), name, category, float(rate), 10, 10000, 'fas fa-star'))
                conn.commit()
                conn.close()
                flash('Nayi service kamyabi se add ho gayi hai!', 'success')
            except Exception as e:
                flash(f'Error adding service: {str(e)}', 'danger')
        return redirect(url_for('admin_panel'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        all_users = cursor.fetchall()
        cursor.execute("SELECT orders.*, users.username FROM orders JOIN users ON orders.user_id = users.id ORDER BY orders.id DESC")
        all_orders = cursor.fetchall()
        cursor.execute("SELECT transactions.*, users.username FROM transactions JOIN users ON transactions.user_id = users.id ORDER BY transactions.id DESC")
        all_transactions = cursor.fetchall()
        conn.close()
    except:
        all_users, all_orders, all_transactions = [], [], []

    services_list = get_all_services()
    supplier_balance = get_supplier_balance()
    user = get_user_data(session['user_id'])
    return render_template('admin.html', user=user, all_users=all_users, all_orders=all_orders, all_transactions=all_transactions, services=services_list, supplier_balance=supplier_balance)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
