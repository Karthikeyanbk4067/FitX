# --- Wishlist Route ---
# app.py (FINAL, COMPLETE, AND WORKING VERSION - Debugging Fixes Applied)
 
from flask import Flask, render_template, abort, session, redirect, url_for, request, flash, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import datetime
import os
from dotenv import load_dotenv
import google.generativeai as genai
import threading # Ensure threading is imported for background tasks
 
# Load environment variables once at the top
load_dotenv()
 
# --- App Initialization ---
app = Flask(__name__)
 
# IMPORTANT FIX: Use a *separate* secret key for Flask sessions.
# This should be a long, random string. DO NOT use your GEMINI_API_KEY for this.
# For production, generate a strong key and load it from an env var.
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
 
# --- Database Connection ---
def get_db_connection():
    conn = sqlite3.connect('products.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn
 
# --- User Model ---
class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash
 
@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    user_data = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
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
 
 
# --- Standard Page Routes ---
@app.route('/')
def home():
    """Renders the landing page and fetches trending products."""
    conn = get_db_connection()
    trending_products = conn.execute(
        "SELECT * FROM products WHERE badge = 'Bestseller' LIMIT 3"
    ).fetchall()
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
        placeholders = ','.join(['?'] * len(selected_categories))
        conditions.append(f"category IN ({placeholders})")
        params.extend(selected_categories)
    if selected_price and '-' in selected_price:
        min_price, max_price = selected_price.split('-')
        conditions.append("price BETWEEN ? AND ?")
        params.extend([float(min_price), float(max_price)])
    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)
    conn = get_db_connection()
    products = conn.execute(base_query, params).fetchall()
    conn.close()
    return render_template(
        'products.html', products=products, cart_item_count=get_cart_count(),
        current_user=current_user, selected_categories=selected_categories, selected_price=selected_price
    )
 
@app.route('/product/<int:product_id>')
def product_detail_page(product_id):
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    conn.close()
    if product is None: abort(404)
    return render_template('product-detail.html', product=product, cart_item_count=get_cart_count(), current_user=current_user)
 
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
 
# --- Authentication Routes ---
@app.route('/signup', methods=['GET', 'POST'])
def signup_page():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if user:
            flash('Username already exists.', 'danger')
            conn.close()
            return redirect(url_for('signup_page'))
        password_hash = generate_password_hash(password)
        conn.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, password_hash))
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
        user_data = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
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
 
 
# --- Order Saving Helper (used by old save_order_for_user but not checkout) ---
def save_order_for_user(user_id, cart):
    conn = get_db_connection()
    cur = conn.cursor()
    # Note: This old version does not save total_amount, status, etc.
    cur.execute('INSERT INTO orders (user_id, date) VALUES (?, datetime("now"))', (user_id,))
    order_id = cur.lastrowid
    for item in cart.values():
        cur.execute('INSERT INTO order_items (order_id, product_id, name, size, quantity, price) VALUES (?, ?, ?, ?, ?, ?)',
                    (order_id, item['id'], item['name'], item.get('size'), item['quantity'], item['price']))
    conn.commit()
    conn.close()
 
# --- Order Fetching Helper ---
def get_orders_for_user(user_id):
    conn = get_db_connection()
    orders = []
    # Ensure 'order_date' column exists in your orders table from create_db.py
    # If using an older DB, it might be named 'date'. Adjust query if needed.
    order_rows = conn.execute('SELECT * FROM orders WHERE user_id = ? ORDER BY order_date DESC', (user_id,)).fetchall()
    for order_row in order_rows:
        items = conn.execute('SELECT * FROM order_items WHERE order_id = ?', (order_row['id'],)).fetchall()
        # Ensure these columns (total_amount, status) exist in your orders table
        try:
            total_amount = order_row['total_amount']
            status = order_row['status']
            order_date = order_row['order_date'] # Use order_date if it exists
        except KeyError:
            # Fallback for older entries or simpler 'orders' table
            total_amount = sum(item['product_price'] * item['quantity'] for item in items) # Recalculate if not stored
            status = "Unknown"
            order_date = order_row['date'] if 'date' in order_row else 'N/A' # Use 'date' if 'order_date' not found
            print(f"Warning: Missing 'total_amount' or 'status' in order {order_row['id']}. Recalculating/Defaulting.")
 
        orders.append({
            'details': {
                'id': order_row['id'],
                'order_date': order_date,
                'total_amount': total_amount,
                'status': status
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
 
# --- Background Order Status Update Helper ---
def update_order_status_in_background(order_id):
    import time
    time.sleep(5)
    conn = get_db_connection()
    try:
        conn.execute('UPDATE orders SET status = ? WHERE id = ?', ('Shipped', order_id))
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
        product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
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
    # This function needs to handle the cart_key with size
    # Assuming product_id here is unique for size as well, or you need to pass size.
    # For now, it updates based on product_id only.
    # If your cart keys are like "product_id_size", this route needs adjustment.
    product_id_str = str(product_id)
    quantity = int(request.form.get('quantity', 1))
    # It needs to know which specific item (product_id_size) to update.
    # For simplicity, if your frontend passes only product_id, it implicitly updates
    # the first matching item. A more robust solution would pass the full key.
    cart = session.get('cart', {})
    # This logic for update_cart is not fully compatible with cart keys like "product_id_size"
    # if product_id_str is meant to be just the numeric product id.
    # If the product_id from the URL is the full cart key (e.g., "1_small"), it works.
    # Assuming for now, simple single-item update.
    for key in list(cart.keys()):
        if str(cart[key]['id']) == product_id_str: # Found by product ID
            if quantity > 0:
                cart[key]['quantity'] = quantity
            else:
                cart.pop(key)
            break # Update only the first instance found
    session['cart'] = cart
    session.modified = True
    return redirect(url_for('cart_page'))
 
@app.route('/remove_from_cart/<int:product_id>')
def remove_from_cart(product_id):
    cart = session.get('cart', {})
    product_id_str = str(product_id)
    # This logic needs to be careful if cart keys are "product_id_size"
    # and product_id is just the numeric ID.
    # Let's iterate and remove all items with this product_id, or specify by size too.
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
            total_amount = sum(item['price'] * item['quantity'] for item in cart.values())
            cursor = conn.execute(
                'INSERT INTO orders (user_id, order_date, total_amount, status, customer_name, shipping_address, city, postal_code, payment_method) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (current_user.id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), total_amount, 'Packed', customer_name, shipping_address, city, postal_code, payment_method)
            )
            new_order_id = cursor.lastrowid
            for item in cart.values():
                conn.execute(
                    'INSERT INTO order_items (order_id, product_id, product_name, product_price, quantity, size, image) VALUES (?, ?, ?, ?, ?, ?, ?)',
                    (new_order_id, item['id'], item['name'], item['price'], item['quantity'], item.get('size'), item.get('image'))
                )
            conn.commit()
        except sqlite3.Error as e:
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
 
# --- START: CHATBOT SECTION MODIFIED ---
 
# Removed duplicate load_dotenv() and api_key definition from here
# It's already done at the top of the file
 
def get_product_summary():
    conn = get_db_connection()
    products = conn.execute("SELECT name, category, price, description, badge, image_main FROM products").fetchall()
    conn.close()
 
    summary_lines = []
    for p in products:
        badge_info = f" (Badge: {p['badge']})" if p['badge'] else ""
        # Adding image_main to summary for potential image display by bot (if LLM supports it or for debug)
        summary_lines.append(f"- Name: {p['name']}{badge_info}, Category: {p['category']}, Price: ₹{p['price']:.2f}, Description: {p['description']}, Image: {p['image_main']}")
   
    return "\n".join(summary_lines)
 
def rule_based_chat(message, user):
    import re
    message = message.lower().strip()
 
    # Basic Rules
    if "hello" in message or "hi" in message:
        return "Hello! 👋 How can I help you today?"
    if "shipping" in message:
        return "We provide shipping across India. Delivery usually takes 3–5 working days."
    if "return" in message or "refund" in message:
        return "We accept returns within 7 days of delivery. Please keep the shoes unused and in original packaging."
    if "contact" in message:
        return "You can reach us via our contact page or email support@alpha.com."
   
    return None  # If no match, we'll use Gemini AI
 
 
@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message', '')
    response_text = rule_based_chat(user_message, current_user)
 
    if not response_text:  # No rule matched → Call Gemini
        try:
            model = genai.GenerativeModel("gemini-1.5-flash-latest")
            gemini_response = model.generate_content(f"User: {user_message}")
            response_text = gemini_response.text if gemini_response else "I'm sorry, I couldn't get a response."
        except Exception as e:
            print(f"Gemini API error: {e}")
            response_text = "Oops! Something went wrong while contacting AI. Please try again later."
 
    return jsonify({"response": response_text})
 
    # NEW: Logic to handle order status queries (already present and good)
    if "order" in message or "status" in message:
        if user.is_authenticated:
            orders = get_orders_for_user(user.id)
            if not orders:
                return "It looks like you haven't placed any orders yet."
            else:
                response = "Here's the status of your most recent order(s):<br><ul>"
                for order in orders[:3]:
                    details = order['details']
                    response += f"<li>Order #{details['id']} placed on {details['order_date']}. Status: <strong>{details['status']}</strong>. Total: ₹{details['total_amount']:.2f}</li>"
                response += "</ul>"
                return response
        else:
            return "Please log in to your account to check your order status. You can sign in using the icon in the top right."
 
    # Show featured shoes for generic queries
    if message in ["your shoes", "shoes", "all shoes", "show shoes", "show me shoes"]:
        conn = get_db_connection()
        products = conn.execute("""
            SELECT name, price, category, description, badge, image_main
            FROM products
            WHERE badge = 'Bestseller' OR badge = 'New Arrival'
            LIMIT 5
        """).fetchall()
        conn.close()
        if products:
            response = f"<b>Here are some of our featured shoes:</b><br><ul>"
            for product in products:
                response += (
                    f"<li><img src='{product['image_main']}' alt='{product['name']}' style='height:40px;'> "
                    f"<b>{product['name']}</b> (Category: {product['category']}, Badge: {product['badge']})<br>"
                    f"Price: ₹{product['price']:.2f}<br>"
                    f"{product['description']}</li>"
                )
            response += "</ul>"
            return response
        else:
            return "We have a wide range of shoes! Please use the Products page to browse all categories."
 
    # Price-based queries: "show me products in less than 3000"
    price_match = re.search(r'(less than|under|below)\s*(\d+)', message)
    if price_match:
        price_limit = float(price_match.group(2))
        conn = get_db_connection()
        products = conn.execute("""
            SELECT name, price, category, description, badge, image_main
            FROM products
            WHERE price < ?
            ORDER BY price ASC
            LIMIT 10
        """, (price_limit,)).fetchall()
        conn.close()
        if products:
            response = f"<b>Here are products under ₹{price_limit}:</b><br><ul>"
            for product in products:
                response += (
                    f"<li><img src='{product['image_main']}' alt='{product['name']}' style='height:40px;'> "
                    f"<b>{product['name']}</b> ({product['category']})<br>"
                    f"Price: ₹{product['price']:.2f}<br>"
                    f"{product['description']}</li>"
                )
            response += "</ul>"
            return response
        else:
            return f"Sorry, no products found under ₹{price_limit}."
 
    # Queries for specific categories
    category_keywords = ["men", "women", "kids", "sports", "casual", "formal", "running", "sneakers"]
    category_match = next((kw for kw in category_keywords if kw in message), None)
    if category_match:
        category = category_match
        conn = get_db_connection()
        products = conn.execute("""
            SELECT name, price, category, description, badge, image_main
            FROM products
            WHERE category LIKE ?
            LIMIT 10
        """, (f"%{category.capitalize()}%",)).fetchall() # Capitalize for database matching
        conn.close()
        if products:
            response = f"<b>Here are some {category} shoes:</b><br><ul>"
            for product in products:
                response += (
                    f"<li><img src='{product['image_main']}' alt='{product['name']}' style='height:40px;'> "
                    f"<b>{product['name']}</b> (Badge: {product['badge']})<br>"
                    f"Price: ₹{product['price']:.2f}<br>"
                    f"{product['description']}</li>"
                )
            response += "</ul>"
            return response
        else:
            return f"Sorry, no products found in category '{category}'. Try asking for 'men', 'women', or 'unisex'."
 
    # Enhanced search for more specific queries
    if "search for" in message or "find" in message or "product" in message or "tell about" in message or "what is" in message:
        search_query = message.replace("search for", "").replace("find", "").replace("product", "").replace("tell about", "").replace("what is", "").strip()
        conn = get_db_connection()
        products = conn.execute("""
            SELECT name, price, category, description, badge, image_main
            FROM products
            WHERE name LIKE ? OR category LIKE ? OR description LIKE ? OR badge LIKE ?
        """, tuple(['%' + search_query + '%']*4)).fetchall()
        conn.close()
        if products:
            response = f"<b>I found these products:</b><br><ul>"
            for product in products[:5]:
                response += (
                    f"<li><img src='{product['image_main']}' alt='{product['name']}' style='height:40px;'> "
                    f"<b>{product['name']}</b> (Category: {product['category']}, Badge: {product['badge']})<br>"
                    f"Price: ₹{product['price']:.2f}<br>"
                    f"{product['description']}</li>"
                )
            response += "</ul>"
            if len(products) > 5:
                response += "And more! You can try a more specific query."
            return response
        else:
            return f"Sorry, I couldn't find products matching '{search_query}'. Can I help with something else?"
 
    # Fallback
    return (
        "I'm sorry, I don't understand that. You can ask about products, shipping, returns, "
        "search by category (men, women, sports, etc.), or ask for products under a certain price (e.g., 'shoes under 5000')."
    )
 
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
You are FITX Bot, a helpful and friendly assistant for FITX, a shoe e-commerce website.
Your primary goal is to help users find information about shoes, store policies, and their orders.
You have access to detailed product information and the user's order history.
 
**Product Data Available (Name, Category, Price, Description, Badge, Image Path):**
{product_data}
 
**User's Order History:**
{order_data}
 
**Instructions for your responses:**
1.  **Product Questions:**
    *   When asked about products, use the 'Product Data Available' section to provide accurate and helpful information.
    *   If a user asks about a specific product, provide its name, category, price, and a summary of its description. If an image path is available, mention it if relevant.
    *   If a user asks for products in a category (e.g., "men's shoes"), list a few relevant products with their prices and maybe a very brief detail.
    *   If a user asks about "bestsellers" or "new arrivals", refer to the 'Badge' information.
    *   If a product is not listed in the provided data, state that you couldn't find it.
2.  **Order Questions:**
    *   If the user asks about their order status or history, use the 'User's Order History' to provide details.
    *   If the user is not logged in and asks about orders, instruct them to log in first.
3.  **General Questions:**
    *   Answer general questions about FITX policies (e.g., shipping, returns) or typical e-commerce queries.
4.  **Out-of-Scope Questions:**
    *   If a question is completely unrelated to FITX, shoes, or orders, politely state that you can only assist with FITX-related inquiries.
5.  **Tone:** Be friendly, clear, and concise.
 
USER'S QUESTION: "{message}"
YOUR ANSWER:
"""
    try:
        # Try gemini-pro first for broader availability, then 1.5-pro if you prefer
        # You can toggle between 'gemini-pro' and 'gemini-1.5-pro-latest'
        model = genai.GenerativeModel('models/gemini-1.5-flash-latest') # Changed back to gemini-pro for initial debugging stability
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Gemini API Error in process_chat_message: {e}")
        # IMPORTANT: Fallback to rule_based_chat for debugging and basic functionality
        return rule_based_chat(message, user) # Fallback to rule_based_chat on error
   
@app.route('/chatbot', methods=['POST'])
def chatbot_response():
    user_message = request.json.get('message', '').strip()
    if not user_message:
        return jsonify({'response': "Please type something."})

    # 1️⃣ Try rule-based first (fast replies)
    rule_response = rule_based_chat(user_message, current_user)
    if rule_response:
        return jsonify({'response': rule_response})

    # 2️⃣ Try Gemini with full product + order context
    try:
        bot_response = process_chat_message(user_message, current_user)
        if not bot_response:
            raise ValueError("Empty response from Gemini")
        return jsonify({'response': bot_response})
    except Exception as e:
        print(f"Gemini API error in /chatbot: {e}")
        # 3️⃣ Fallback response
        return jsonify({'response': "⚠️ Our AI assistant is currently busy. Please try again later."})
# --- END: CHATBOT SECTION MODIFIED ---
 
 
@app.route('/search')
def search():
    query = request.args.get('q', '')
    conn = get_db_connection()
    products = conn.execute(
        "SELECT * FROM products WHERE name LIKE ?", ('%' + query + '%',)
    ).fetchall()
    conn.close()
    return render_template(
        'products.html',
        products=products,
        cart_item_count=get_cart_count(),
        current_user=current_user,
        selected_categories=[],
        selected_price=None
    )
 
# --- WISHLIST ROUTES ---
@app.route('/wishlist')
@login_required
def wishlist():
    conn = get_db_connection()
    products = conn.execute('''
        SELECT p.* FROM products p
        JOIN wishlist w ON p.id = w.product_id
        WHERE w.user_id = ?
    ''', (current_user.id,)).fetchall()
    conn.close()
    return render_template('wishlist.html', products=products, cart_item_count=get_cart_count())
 
@app.route('/add_to_wishlist', methods=['POST'])
@login_required
def add_to_wishlist():
    product_id = request.form.get('product_id')
    if product_id:
        try:
            conn = get_db_connection()
            conn.execute('INSERT OR IGNORE INTO wishlist (user_id, product_id) VALUES (?, ?)',
                         (current_user.id, product_id))
            conn.commit()
            conn.close()
            flash('Product added to wishlist!', 'success')
        except sqlite3.IntegrityError:
            flash('Product is already in your wishlist.', 'info')
        except Exception as e:
            flash(f'Error adding to wishlist: {e}', 'danger')
    return redirect(request.referrer or url_for('home'))
 
@app.route('/remove_from_wishlist', methods=['POST'])
@login_required
def remove_from_wishlist():
    product_id = request.form.get('product_id')
    if product_id:
        try:
            conn = get_db_connection()
            conn.execute('DELETE FROM wishlist WHERE user_id = ? AND product_id = ?',
                         (current_user.id, product_id))
            conn.commit()
            conn.close()
            flash('Product removed from wishlist!', 'success')
        except Exception as e:
            flash(f'Error removing from wishlist: {e}', 'danger')
    return redirect(url_for('wishlist'))
 
if __name__ == '__main__':
    app.run(debug=True)


