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
# app.py (MODIFIED)

# ... (all your imports should be at the top)
from whitenoise import WhiteNoise

# Load environment variables once at the top
load_dotenv()
 
# --- App Initialization ---
app = Flask(__name__)

# --- FINAL, ROBUST WHITENOISE CONFIGURATION ---
# Construct the absolute path to the 'static' directory
static_folder_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
# Configure WhiteNoise with the absolute path and the correct prefix
app.wsgi_app = WhiteNoise(app.wsgi_app, root=static_folder_root, prefix="static/")
# -------------------------------------------

# IMPORTANT FIX: Use a *separate* secret key for Flask sessions.
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your_super_secret_fallback_key_CHANGE_THIS_IN_PROD')

# ... (the rest of your app.py file continues as normal)
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
                'price': float(product['price']),
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
 
# ===================================================================
# START: UPGRADED CHATBOT LOGIC (DATABASE-CONNECTED & AI-POWERED)
# ===================================================================

import re # Make sure 're' is imported at the top of your app.py file

# --- TOOL 1: DATABASE FUNCTION FOR PRODUCT SEARCHES ---
def search_products_db(query: str = None, min_price: float = None, max_price: float = None):
    """
    Searches the database for products. Can filter by a search query (name/category),
    a minimum price, a maximum price, or any combination of these.
    This is a tool for the AI chatbot.
    """
    conn = get_db_connection() # Connects to your Render PostgreSQL database
    
    # Start building the SQL query dynamically and safely
    base_query = "SELECT name, price, category, description FROM products"
    conditions = []
    params = []

    if query:
        conditions.append("(name ILIKE %s OR category ILIKE %s)")
        params.extend([f"%{query}%", f"%{query}%"])
    
    if min_price is not None:
        conditions.append("price >= %s")
        params.append(min_price)
        
    if max_price is not None:
        conditions.append("price <= %s")
        params.append(max_price)

    # Combine conditions if any exist
    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)
    
    base_query += " LIMIT 5" # Always limit results to avoid overwhelming the AI

    # Execute the query against the live database
    with conn.cursor(cursor_factory=DictCursor) as cur:
        cur.execute(base_query, params)
        products = cur.fetchall()
    conn.close()

    if not products:
        # Provide a more helpful "not found" message
        search_term = f"matching '{query}'" if query else ""
        price_term = ""
        if min_price is not None and max_price is not None:
            price_term = f"between ₹{min_price} and ₹{max_price}"
        elif max_price is not None:
            price_term = f"under ₹{max_price}"
        elif min_price is not None:
            price_term = f"over ₹{min_price}"
        
        return f"I couldn't find any products {search_term} {price_term}. Please try different criteria."

    # Format the results into a clean string for the AI to understand
    results_string = "I found these products:\n"
    for p in products:
        results_string += f"- Name: {p['name']}, Category: {p['category']}, Price: ₹{float(p['price']):.2f}\n"
    return results_string

# --- TOOL 2: DATABASE FUNCTION FOR ORDER STATUS ---
def get_order_status_db(order_id: int, user_id: int):
    """
    Gets the status and details of a specific order for a given user from the Render database.
    This is a tool for the AI chatbot.
    """
    conn = get_db_connection() # Connects to your Render PostgreSQL database
    with conn.cursor(cursor_factory=DictCursor) as cur:
        cur.execute("SELECT id, status, order_date, total_amount FROM orders WHERE id = %s AND user_id = %s", (order_id, user_id))
        order = cur.fetchone()
    conn.close()

    if not order:
        return f"I couldn't find any order with the ID #{order_id} for this user. They might have the wrong ID or are not logged in."

    # Format the result into a clean string for the AI to understand
    return f"Order #{order['id']} Status: {order['status']}, Order Date: {order['order_date'].strftime('%Y-%m-%d')}, Total: ₹{float(order['total_amount']):.2f}."

# --- FALLBACK: SIMPLE RULE-BASED CHAT ---
def rule_based_chat(message, user):
    """Handles simple, fixed questions for a fast, free response."""
    message = message.lower().strip()
    if "hello" in message or "hi" in message: return "Hello! 👋 I'm the FITX Bot. How can I help you with our footwear today?"
    if "shipping" in message: return "We provide shipping across India. Delivery usually takes 3–5 working days."
    if "return" in message or "refund" in message: return "We accept returns within 30 days of delivery for unused items in their original packaging."
    if "contact" in message: return "You can reach our human team via the 'Contact Us' page on our website."
    return None

# --- THE "BRAIN": MAIN AI LOGIC WITH TOOL-USING CAPABILITIES ---
def process_chat_message(message, user):
    """
    Processes a user's message using the Gemini API, decides if a database tool is needed,
    executes it against the Render DB, and then generates a final natural language response.
    """
    system_prompt = f"""
You are FITX Bot, a helpful and friendly e-commerce assistant for a shoe store.
Your goal is to answer the user's question about the store's products and their orders.

Today's Date: {datetime.now().strftime('%Y-%m-%d')}

TOOLS AVAILABLE:
1. search_products(query: str = None, min_price: float = None, max_price: float = None): Use this to search for products. You can search by a text query, a price range, or both. For example, to find shoes under 10000, call it with max_price=10000. To find 'running shoes' over 8000, call it with query='running shoes' and min_price=8000.
2. get_order_status(order_id: int): Use this to get the status of a specific order for a logged-in user.

USER CONTEXT:
- The user is {'LOGGED IN as user_id ' + str(user.id) if user.is_authenticated else 'NOT LOGGED IN'}.

INSTRUCTIONS:
1. **CRITICAL RULE:** Your ONLY purpose is to assist with the FITX shoe store. If the user asks any question that is NOT about our products, their orders, shipping, or store policies (e.g., asking for jokes, math problems, general knowledge, other companies), you MUST politely refuse. A perfect refusal is: "I'm the FITX Bot, and my expertise is limited to our products and your orders. How can I help you with our footwear today?"
2. Analyze the user's question to see if it's related to our store.
3. If you need to look up product information (like price or availability), respond ONLY with: [TOOL_CALL] search_products(...)
4. If you need to look up an order status, respond ONLY with: [TOOL_CALL] get_order_status(...)
5. If the question is simple and on-topic (e.g., "What are your return policies?"), you can answer it directly.
6. If you call a tool, I will provide the result, and you must then formulate a final, friendly answer to the user based on that information.
"""

    initial_prompt = f"{system_prompt}\nUser's Question: \"{message}\"\n\nYour Response:"
    
    try:
        model = genai.GenerativeModel("gemini-1.5-flash-latest")
        initial_response = model.generate_content(initial_prompt)
        ai_decision = initial_response.text.strip()

        if ai_decision.startswith("[TOOL_CALL]"):
            print(f"AI decided to call a tool: {ai_decision}")
            tool_result = ""
            
            tool_match = re.search(r'search_products\((.*?)\)', ai_decision)
            order_match = re.search(r'get_order_status\(order_id=(\d+)\)', ai_decision)

            if tool_match:
                args_str = tool_match.group(1)
                query_arg = re.search(r'query="([^"]+)"', args_str)
                min_price_arg = re.search(r'min_price=([\d\.]+)', args_str)
                max_price_arg = re.search(r'max_price=([\d\.]+)', args_str)
                
                query = query_arg.group(1) if query_arg else None
                min_price = float(min_price_arg.group(1)) if min_price_arg else None
                max_price = float(max_price_arg.group(1)) if max_price_arg else None
                
                tool_result = search_products_db(query=query, min_price=min_price, max_price=max_price)
                
            elif order_match:
                if not user.is_authenticated:
                    return "You need to be logged in for me to check your order status."
                order_id = int(order_match.group(1))
                tool_result = get_order_status_db(order_id=order_id, user_id=user.id)
            else:
                tool_result = "An error occurred trying to use that tool."

            final_prompt = f"{system_prompt}\nUser's Question: \"{message}\"\nYou decided to call a tool. Here is the result from the database:\n[TOOL_RESULT]\n{tool_result}\n\nNow, please provide a final, friendly, and natural-sounding answer to the user based on this information."
            final_response = model.generate_content(final_prompt)
            return final_response.text.strip()
        else:
            return ai_decision

    except Exception as e:
        print(f"Gemini API Error in process_chat_message: {e}")
        return rule_based_chat(message, user) or "I'm sorry, I had a little trouble processing that. Could you try asking in a different way?"

# --- FLASK ROUTE: THE CHATBOT ENDPOINT ---
@app.route('/chatbot', methods=['POST'])
def chatbot_response():
    user_message = request.json.get('message', '').strip()
    if not user_message:
        return jsonify({'response': "Please type something."})
    
    # First, try the simple rule-based chat for instant answers
    rule_response = rule_based_chat(user_message, current_user)
    if rule_response:
        return jsonify({'response': rule_response})
    
    # If no rule matches, use the advanced AI logic
    try:
        bot_response = process_chat_message(user_message, current_user)
        if not bot_response: raise ValueError("Empty response from Gemini")
        return jsonify({'response': bot_response})
    except Exception as e:
        print(f"Major error in /chatbot route: {e}")
        return jsonify({'response': "⚠️ Our AI assistant is currently busy. Please try again in a moment."})

# ===================================================================
# END: UPGRADED CHATBOT LOGIC
# ===================================================================
 
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
 

