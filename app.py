# app.py (MODIFIED FOR POSTGRESQL ON RENDER)
 
from flask import Flask, render_template, abort, session, redirect, url_for, request, flash, jsonify
# import sqlite3 # --- REMOVED ---
import psycopg2 # --- ADDED for PostgreSQL
from psycopg2.extras import DictCursor # --- ADDED to get dict-like rows
from urllib.parse import urlparse # --- ADDED to parse the database URL
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import datetime
import os
from dotenv import load_dotenv
import google.generativeai as genai
import threading # Ensure threading is imported for background tasks
from whitenoise import WhiteNoise # <--- 1. IMPORT WHITENOISE HERE

# Load environment variables once at the top
load_dotenv()
 
# --- App Initialization ---
app = Flask(__name__)

# --- 2. ADD THIS LINE AFTER APP INITIALIZATION ---
# This tells WhiteNoise to look for a 'static' folder and serve its contents
app.wsgi_app = WhiteNoise(app.wsgi_app, root='static/')

# IMPORTANT FIX: Use a *separate* secret key for Flask sessions.
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your_super_secret_fallback_key_CHANGE_THIS_IN_PROD')
 
# Configure Gemini API
api_key = os.environ.get('GEMINI_API_KEY')
if not api_key:
    print("ERROR: GEMINI_API_KEY not found in environment variables. Chatbot will not work.")
else:
    print(f"Loaded GEMINI_API_KEY (first time check): {api_key}")
    genai.configure(api_key=api_key)
 
 
# --- Flask-Login Setup ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login_page'
login_manager.login_message_category = "danger"
 
# --- START: DATABASE CONNECTION MODIFIED FOR POSTGRESQL ---
def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable is not set.")
    
    # Parse the database URL
    result = urlparse(db_url)
    username = result.username
    password = result.password
    database = result.path[1:]
    hostname = result.hostname
    port = result.port
    
    conn = psycopg2.connect(
        dbname=database,
        user=username,
        password=password,
        host=hostname,
        port=port
    )
    return conn
# --- END: DATABASE CONNECTION MODIFIED FOR POSTGRESQL ---
 
# --- User Model ---
class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash
 
@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    # --- MODIFIED: Use psycopg2 cursor and %s placeholder ---
    with conn.cursor(cursor_factory=DictCursor) as cur:
        cur.execute('SELECT * FROM users WHERE id = %s', (user_id,))
        user_data = cur.fetchone()
    conn.close()
    if user_data:
        return User(id=user_data['id'], username=user_data['username'], password_hash=user_data['password_hash'])
    return None
 
# --- Helper Function for Cart ---
def get_cart_count():
    return len(session.get('cart', {}))
 
@app.context_processor
def inject_current_year():
    """Injects the current year into all templates."""
    return {'current_year': datetime.utcnow().year}
 
 
# --- Standard Page Routes (with DB logic updated) ---
@app.route('/')
def home():
    """Renders the landing page and fetches trending products."""
    conn = get_db_connection()
    # --- MODIFIED: Use psycopg2 cursor and %s placeholder ---
    with conn.cursor(cursor_factory=DictCursor) as cur:
        cur.execute("SELECT * FROM products WHERE badge = 'Bestseller' LIMIT 3")
        trending_products = cur.fetchall()
    conn.close()
    return render_template(
        'index.html',
        cart_item_count=get_cart_count(),
        current_user=current_user,
        trending_products=trending_products
    )
 
@app.route('/products')
def products_page():
    selected_categories = request.args.getlist('category')
    selected_price = request.args.get('price')
    base_query = "SELECT * FROM products"
    conditions = []
    params = []
    if selected_categories:
        placeholders = ','.join(['%s'] * len(selected_categories)) # Use %s
        conditions.append(f"category IN ({placeholders})")
        params.extend(selected_categories)
    if selected_price and '-' in selected_price:
        min_price, max_price = selected_price.split('-')
        conditions.append("price BETWEEN %s AND %s") # Use %s
        params.extend([float(min_price), float(max_price)])
    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)
    
    conn = get_db_connection()
    # --- MODIFIED: Use psycopg2 cursor ---
    with conn.cursor(cursor_factory=DictCursor) as cur:
        cur.execute(base_query, params)
        products = cur.fetchall()
    conn.close()
    return render_template(
        'products.html', products=products, cart_item_count=get_cart_count(),
        current_user=current_user, selected_categories=selected_categories, selected_price=selected_price
    )
 
@app.route('/product/<int:product_id>')
def product_detail_page(product_id):
    conn = get_db_connection()
    # --- MODIFIED: Use psycopg2 cursor and %s placeholder ---
    with conn.cursor(cursor_factory=DictCursor) as cur:
        cur.execute('SELECT * FROM products WHERE id = %s', (product_id,))
        product = cur.fetchone()
    conn.close()
    if product is None: abort(404)
    return render_template('product-detail.html', product=product, cart_item_count=get_cart_count(), current_user=current_user)
 
# --- Static Page Routes (No DB interaction, no changes needed) ---
@app.route('/our-story')
def our_story_page():
    return render_template('our-story.html', cart_item_count=get_cart_count(), current_user=current_user)
 
@app.route('/careers')
def careers_page():
    return render_template('careers.html', cart_item_count=get_cart_count(), current_user=current_user)
 
@app.route('/press')
def press_page():
    return render_template('press.html', cart_item_count=get_cart_count(), current_user=current_user)
 
@app.route('/sustainability')
def sustainability_page():
    return render_template('sustainability.html', cart_item_count=get_cart_count(), current_user=current_user)
 
@app.route('/contact')
def contact_page():
    return render_template('contact.html', cart_item_count=get_cart_count(), current_user=current_user)
 
@app.route('/faq')
def faq_page():
    return render_template('faq.html', cart_item_count=get_cart_count(), current_user=current_user)
 
# --- Authentication Routes (with DB logic updated) ---
@app.route('/signup', methods=['GET', 'POST'])
def signup_page():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        conn = get_db_connection()
        # --- MODIFIED: Use psycopg2 cursor and %s placeholder ---
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute('SELECT * FROM users WHERE username = %s', (username,))
            user = cur.fetchone()
            if user:
                flash('Username already exists.', 'danger')
                conn.close()
                return redirect(url_for('signup_page'))
            
            password_hash = generate_password_hash(password)
            cur.execute('INSERT INTO users (username, password_hash) VALUES (%s, %s)', (username, password_hash))
            conn.commit()
        conn.close()
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login_page'))
    return render_template('signup.html', cart_item_count=get_cart_count(), current_user=current_user)
 
@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        conn = get_db_connection()
        # --- MODIFIED: Use psycopg2 cursor and %s placeholder ---
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute('SELECT * FROM users WHERE username = %s', (username,))
            user_data = cur.fetchone()
        conn.close()
        
        if user_data and check_password_hash(user_data['password_hash'], password):
            user_to_login = User(id=user_data['id'], username=user_data['username'], password_hash=user_data['password_hash'])
            login_user(user_to_login)
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password.', 'danger')
            return redirect(url_for('login_page'))
    return render_template('login.html', cart_item_count=get_cart_count(), current_user=current_user)
 
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))
 
# Note: The original file has two different save_order functions. I've updated both.
# The `save_order_for_user` function seems unused by the checkout flow, but is updated for consistency.
def save_order_for_user(user_id, cart):
    conn = get_db_connection()
    with conn.cursor() as cur:
        # Note: NOW() is PostgreSQL for current timestamp
        cur.execute('INSERT INTO orders (user_id, date) VALUES (%s, NOW()) RETURNING id', (user_id,))
        order_id = cur.fetchone()[0]
        for item in cart.values():
            cur.execute('INSERT INTO order_items (order_id, product_id, name, size, quantity, price) VALUES (%s, %s, %s, %s, %s, %s)',
                        (order_id, item['id'], item['name'], item.get('size'), item['quantity'], item['price']))
        conn.commit()
    conn.close()
 
def get_orders_for_user(user_id):
    conn = get_db_connection()
    orders = []
    with conn.cursor(cursor_factory=DictCursor) as cur:
        cur.execute('SELECT * FROM orders WHERE user_id = %s ORDER BY order_date DESC', (user_id,))
        order_rows = cur.fetchall()
        for order_row in order_rows:
            cur.execute('SELECT * FROM order_items WHERE order_id = %s', (order_row['id'],))
            items = cur.fetchall()
            
            orders.append({
                'details': {
                    'id': order_row['id'],
                    'order_date': order_row['order_date'],
                    'total_amount': order_row['total_amount'],
                    'status': order_row['status']
                },
                'items': items
            })
    conn.close()
    return orders
 
@app.route('/account')
@login_required
def account_page():
    orders = get_orders_for_user(current_user.id)
    return render_template('account.html', cart_item_count=get_cart_count(), current_user=current_user, orders=orders)
 
def update_order_status_in_background(order_id):
    import time
    time.sleep(5)
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('UPDATE orders SET status = %s WHERE id = %s', ('Shipped', order_id))
            conn.commit()
    finally:
        conn.close()
 
@app.route('/cart')
def cart_page():
    cart_items = session.get('cart', {}).values()
    total_price = sum(item['price'] * item['quantity'] for item in cart_items)
    return render_template('cart.html', cart_items=list(cart_items), total_price=total_price, cart_item_count=get_cart_count(), current_user=current_user)
 
@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    product_id = request.form.get('product_id')
    selected_size = request.form.get('selected_size')
    cart = session.get('cart', {})
    product_id_str = str(product_id)
    found = False
    for key, item in cart.items():
        if item['id'] == int(product_id) and item.get('size') == selected_size:
            cart[key]['quantity'] += 1
            found = True
            break
    if not found:
        conn = get_db_connection()
        # --- MODIFIED: Use psycopg2 cursor and %s placeholder ---
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute('SELECT * FROM products WHERE id = %s', (product_id,))
            product = cur.fetchone()
        conn.close()
        
        if product:
            cart_key = f"{product_id_str}_{selected_size}"
            cart[cart_key] = {
                'id': product['id'],
                'name': product['name'],
                'price': product['price'],
                'image': product['image_main'],
                'quantity': 1,
                'size': selected_size
            }
    session['cart'] = cart
    session.modified = True
    return redirect(url_for('cart_page'))
 
@app.route('/update_cart/<int:product_id>', methods=['POST'])
def update_cart(product_id):
    product_id_str = str(product_id)
    quantity = int(request.form.get('quantity', 1))
    cart = session.get('cart', {})
    for key in list(cart.keys()):
        if str(cart[key]['id']) == product_id_str:
            if quantity > 0:
                cart[key]['quantity'] = quantity
            else:
                cart.pop(key)
            break
    session['cart'] = cart
    session.modified = True
    return redirect(url_for('cart_page'))
 
@app.route('/remove_from_cart/<int:product_id>')
def remove_from_cart(product_id):
    cart = session.get('cart', {})
    product_id_str = str(product_id)
    keys_to_remove = [key for key in cart if str(cart[key]['id']) == product_id_str]
    for key in keys_to_remove:
        cart.pop(key)
    session['cart'] = cart
    session.modified = True
    return redirect(url_for('cart_page'))
 
@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout_page():
    cart = session.get('cart', {})
    if not cart:
        flash("Your cart is empty.", "info")
        return redirect(url_for('products_page'))
 
    if request.method == 'POST':
        customer_name = request.form.get('customer_name')
        shipping_address = request.form.get('shipping_address')
        city = request.form.get('city')
        postal_code = request.form.get('postal_code')
        payment_method = request.form.get('payment_method')
        conn = get_db_connection()
        new_order_id = None
        try:
            with conn.cursor() as cur:
                total_amount = sum(item['price'] * item['quantity'] for item in cart.values())
                # --- MODIFIED: Use RETURNING id to get the new order's ID ---
                cur.execute(
                    'INSERT INTO orders (user_id, order_date, total_amount, status, customer_name, shipping_address, city, postal_code, payment_method) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id',
                    (current_user.id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), total_amount, 'Packed', customer_name, shipping_address, city, postal_code, payment_method)
                )
                new_order_id = cur.fetchone()[0] # Fetch the returned ID
                
                for item in cart.values():
                    cur.execute(
                        'INSERT INTO order_items (order_id, product_id, product_name, product_price, quantity, size, image) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                        (new_order_id, item['id'], item['name'], item['price'], item['quantity'], item.get('size'), item.get('image'))
                    )
                conn.commit()
        except psycopg2.Error as e: # Catch psycopg2 errors
            conn.rollback()
            print(f"DB error during checkout: {e}")
            flash('There was an error placing your order. Please try again.', 'danger')
            return redirect(url_for('cart_page'))
        finally:
            conn.close()
 
        if new_order_id:
            thread = threading.Thread(target=update_order_status_in_background, args=(new_order_id,), daemon=True)
            thread.start()
 
        session['ordered_items'] = list(cart.values())
        session.pop('cart', None)
        return redirect(url_for('checkout_success'))
 
    cart_items = list(cart.values())
    total_price = sum(item['price'] * item['quantity'] for item in cart_items)
    return render_template('checkout.html', cart_items=cart_items, total_price=total_price, cart_item_count=len(cart_items), current_user=current_user)
 
@app.route('/checkout-success')
@login_required
def checkout_success():
    ordered_items = session.pop('ordered_items', [])
    if not ordered_items:
        return redirect(url_for('home'))
    return render_template('checkout-success.html', ordered_items=ordered_items, cart_item_count=0, current_user=current_user)
 
# --- CHATBOT SECTION (with DB logic updated) ---
 
def get_product_summary():
    conn = get_db_connection()
    # --- MODIFIED: Use psycopg2 cursor ---
    with conn.cursor(cursor_factory=DictCursor) as cur:
        cur.execute("SELECT name, category, price, description, badge, image_main FROM products")
        products = cur.fetchall()
    conn.close()
 
    summary_lines = []
    for p in products:
        badge_info = f" (Badge: {p['badge']})" if p['badge'] else ""
        summary_lines.append(f"- Name: {p['name']}{badge_info}, Category: {p['category']}, Price: ₹{p['price']:.2f}, Description: {p['description']}, Image: {p['image_main']}")
   
    return "\n".join(summary_lines)

# The rest of the chatbot logic does not directly use the database connection object,
# but relies on helper functions like get_orders_for_user and get_product_summary,
# which have already been updated. So, no further changes are needed in the chatbot routes themselves.
# The original file's chatbot routes are maintained below.
def rule_based_chat(message, user):
    import re
    message = message.lower().strip()
    if "hello" in message or "hi" in message: return "Hello! 👋 How can I help you today?"
    if "shipping" in message: return "We provide shipping across India. Delivery usually takes 3–5 working days."
    if "return" in message or "refund" in message: return "We accept returns within 7 days of delivery. Please keep the shoes unused and in original packaging."
    if "contact" in message: return "You can reach us via our contact page or email support@alpha.com."
    return None

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message', '')
    response_text = rule_based_chat(user_message, current_user)
    if not response_text:
        try:
            model = genai.GenerativeModel("gemini-1.5-flash-latest")
            gemini_response = model.generate_content(f"User: {user_message}")
            response_text = gemini_response.text if gemini_response else "I'm sorry, I couldn't get a response."
        except Exception as e:
            print(f"Gemini API error: {e}")
            response_text = "Oops! Something went wrong while contacting AI. Please try again later."
    return jsonify({"response": response_text})

def process_chat_message(message, user):
    product_data = get_product_summary()
    order_data = "User is not logged in."
    if user.is_authenticated:
        orders = get_orders_for_user(user.id)
        if orders:
            order_data = "Here is the user's recent order history:\n"
            for order in orders[:3]:
                details = order['details']
                order_data += f"- Order ID {details['id']}, Status: {details['status']}, Total: ₹{details['total_amount']:.2f}, Order Date: {details['order_date']}\n"
        else:
            order_data = "The user has no past orders."
    prompt = f"""
You are FITX Bot... [rest of prompt is unchanged]
USER'S QUESTION: "{message}"
YOUR ANSWER:
"""
    try:
        model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Gemini API Error in process_chat_message: {e}")
        return rule_based_chat(message, user)

@app.route('/chatbot', methods=['POST'])
def chatbot_response():
    user_message = request.json.get('message', '').strip()
    if not user_message: return jsonify({'response': "Please type something."})
    rule_response = rule_based_chat(user_message, current_user)
    if rule_response: return jsonify({'response': rule_response})
    try:
        bot_response = process_chat_message(user_message, current_user)
        if not bot_response: raise ValueError("Empty response from Gemini")
        return jsonify({'response': bot_response})
    except Exception as e:
        print(f"Gemini API error in /chatbot: {e}")
        return jsonify({'response': "⚠️ Our AI assistant is currently busy. Please try again later."})
 
# --- Search Route (with DB logic updated) ---
@app.route('/search')
def search():
    query = request.args.get('q', '')
    conn = get_db_connection()
    # --- MODIFIED: Use psycopg2 cursor and %s placeholder ---
    with conn.cursor(cursor_factory=DictCursor) as cur:
        cur.execute("SELECT * FROM products WHERE name LIKE %s", ('%' + query + '%',))
        products = cur.fetchall()
    conn.close()
    return render_template(
        'products.html',
        products=products,
        cart_item_count=get_cart_count(),
        current_user=current_user,
        selected_categories=[],
        selected_price=None
    )
 
# --- WISHLIST ROUTES (with DB logic updated) ---
@app.route('/wishlist')
@login_required
def wishlist():
    conn = get_db_connection()
    # --- MODIFIED: Use psycopg2 cursor and %s placeholder ---
    with conn.cursor(cursor_factory=DictCursor) as cur:
        cur.execute('''
            SELECT p.* FROM products p
            JOIN wishlist w ON p.id = w.product_id
            WHERE w.user_id = %s
        ''', (current_user.id,))
        products = cur.fetchall()
    conn.close()
    return render_template('wishlist.html', products=products, cart_item_count=get_cart_count())
 
@app.route('/add_to_wishlist', methods=['POST'])
@login_required
def add_to_wishlist():
    product_id = request.form.get('product_id')
    if product_id:
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                # --- MODIFIED: Changed INSERT OR IGNORE to PostgreSQL's ON CONFLICT DO NOTHING ---
                # This assumes you have a unique constraint on (user_id, product_id) in your wishlist table.
                cur.execute('''
                    INSERT INTO wishlist (user_id, product_id) VALUES (%s, %s)
                    ON CONFLICT (user_id, product_id) DO NOTHING
                ''', (current_user.id, product_id))
                conn.commit()
            conn.close()
            flash('Product added to wishlist!', 'success')
        except psycopg2.Error as e: # Catch psycopg2 errors
            flash(f'Error adding to wishlist: {e}', 'danger')
    return redirect(request.referrer or url_for('home'))
 
@app.route('/remove_from_wishlist', methods=['POST'])
@login_required
def remove_from_wishlist():
    product_id = request.form.get('product_id')
    if product_id:
        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                cur.execute('DELETE FROM wishlist WHERE user_id = %s AND product_id = %s',
                             (current_user.id, product_id))
                conn.commit()
            conn.close()
            flash('Product removed from wishlist!', 'success')
        except psycopg2.Error as e: # Catch psycopg2 errors
            flash(f'Error removing from wishlist: {e}', 'danger')
    return redirect(url_for('wishlist'))
 
if __name__ == '__main__':
    app.run(debug=True)
    