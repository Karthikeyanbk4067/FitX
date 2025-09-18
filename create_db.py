# create_db.py (Modified to use psycopg2 for PostgreSQL)

import os
from app import get_db_connection # Import the new connection function from your modified app.py
import psycopg2

# --- Configuration (No changes here) ---
IMAGE_FOLDER_PATH = 'assets/Products/'
IMAGE_EXTENSION = 'jpeg'

# --- Definitive List of 50 Unique Products (No changes here) ---
products_data = [
    {"id": 1, "name": "Alpha Sprint Lite", "category": "Men", "price": 6800, "mrp": 8000, "description": "Lightweight and agile, perfect for sprints.", "badge": "New Arrival"},
    {"id": 2, "name": "Aura Flex Walker", "category": "Women", "price": 7200, "mrp": 8500, "description": "Maximum flexibility for a natural walking experience.", "badge": None},
    {"id": 3, "name": "Element Street Canvas", "category": "Unisex", "price": 7800, "mrp": 9200, "description": "A classic canvas sneaker for timeless street style.", "badge": "Bestseller"},
    {"id": 4, "name": "Terra Glide", "category": "Men", "price": 7950, "mrp": 9500, "description": "A versatile trainer for both gym workouts and light jogs.", "badge": None},
    {"id": 5, "name": "Nova Casual", "category": "Women", "price": 6900, "mrp": 8100, "description": "The perfect blend of comfort and casual elegance.", "badge": None},
    {"id": 6, "name": "Classic Court", "category": "Unisex", "price": 7400, "mrp": 8800, "description": "Inspired by vintage tennis shoes, offering a clean look.", "badge": None},
    {"id": 7, "name": "Pace Runner", "category": "Men", "price": 7600, "mrp": 9000, "description": "A reliable daily runner with balanced cushioning.", "badge": "Bestseller"},
    {"id": 8, "name": "Stellar Slip-On", "category": "Women", "price": 6500, "mrp": 7800, "description": "Effortless style meets all-day comfort.", "badge": None},
    {"id": 9, "name": "Urban Roam", "category": "Unisex", "price": 7900, "mrp": 9400, "description": "Built for city exploration, with a durable sole.", "badge": None},
    {"id": 10, "name": "Active Flow", "category": "Men", "price": 7300, "mrp": 8600, "description": "Breathable mesh and a responsive sole for active lifestyles.", "badge": None},
    {"id": 11, "name": "Bliss Walk", "category": "Women", "price": 7700, "mrp": 9100, "description": "Engineered for superior comfort on long walks.", "badge": "New Arrival"},
    {"id": 12, "name": "Foundation Trainer", "category": "Unisex", "price": 7999, "mrp": 9500, "description": "A solid, all-around training shoe for any workout.", "badge": None},
    {"id": 13, "name": "Metro Commuter", "category": "Men", "price": 7100, "mrp": 8400, "description": "Sleek and professional, for the modern urban commuter.", "badge": None},
    {"id": 14, "name": "Sunset Sandal", "category": "Women", "price": 5800, "mrp": 7000, "description": "An elegant and comfortable sandal for warm evenings.", "badge": None},
    {"id": 15, "name": "Rebel Skate", "category": "Unisex", "price": 7850, "mrp": 9300, "description": "Durable suede and a flat sole for maximum board feel.", "badge": "Bestseller"},
    {"id": 16, "name": "Alpha Runner Pro", "category": "Men", "price": 8999, "mrp": 10999, "description": "Engineered for peak performance, perfect for marathon training.", "badge": "Bestseller"},
    {"id": 17, "name": "Velocity Knit", "category": "Women", "price": 9200, "mrp": 11000, "description": "Lightweight and breathable, for high-intensity workouts.", "badge": None},
    {"id": 18, "name": "Vortex Street High", "category": "Unisex", "price": 11500, "mrp": 13000, "description": "A bold, high-top sneaker that makes a statement.", "badge": "Limited Edition"},
    {"id": 19, "name": "Helios Racer", "category": "Men", "price": 10500, "mrp": 12500, "description": "A feather-light racing flat for competitive runners.", "badge": None},
    {"id": 20, "name": "Lunar Glide Max", "category": "Women", "price": 11800, "mrp": 14000, "description": "Experience cloud-like comfort with maximum cushioning.", "badge": "New Arrival"},
    {"id": 21, "name": "Fusion XT", "category": "Unisex", "price": 9800, "mrp": 11500, "description": "A cross-training powerhouse with stability and flexibility.", "badge": "Bestseller"},
    {"id": 22, "name": "Strato Commute Lux", "category": "Men", "price": 8500, "mrp": 10000, "description": "A smart and stylish shoe for your daily commute.", "badge": None},
    {"id": 23, "name": "Ember Leather", "category": "Women", "price": 11200, "mrp": 13500, "description": "Crafted from premium leather for a luxurious feel.", "badge": None},
    {"id": 24, "name": "Core All-Day", "category": "Unisex", "price": 8200, "mrp": 9800, "description": "The ultimate versatile sneaker, your go-to for any occasion.", "badge": None},
    {"id": 25, "name": "Titanium Trainer X", "category": "Men", "price": 11900, "mrp": 14200, "description": "Maximum support and durability for demanding workouts.", "badge": "Limited Edition"},
    {"id": 26, "name": "Serene Yoga Slip", "category": "Women", "price": 8100, "mrp": 9600, "description": "A minimalist, flexible shoe for studio workouts.", "badge": None},
    {"id": 27, "name": "Echo Hiker Lite", "category": "Unisex", "price": 10800, "mrp": 12800, "description": "A lightweight hiking shoe for day trips and easy trails.", "badge": None},
    {"id": 28, "name": "Momentum Run 2", "category": "Men", "price": 9500, "mrp": 11200, "description": "Feel the energy return with every step.", "badge": "Bestseller"},
    {"id": 29, "name": "Adorn Loafer", "category": "Women", "price": 8800, "mrp": 10500, "description": "A sophisticated loafer for work and casual attire.", "badge": None},
    {"id": 30, "name": "Gridiron Cleat Pro", "category": "Unisex", "price": 11000, "mrp": 13000, "description": "Engineered for traction and speed on the field.", "badge": "New Arrival"},
    {"id": 31, "name": "Stealth Jogger Night", "category": "Men", "price": 9999, "mrp": 12000, "description": "A sleek, all-black design for a modern aesthetic.", "badge": None},
    {"id": 32, "name": "Orion Cross-Trainer", "category": "Unisex", "price": 10200, "mrp": 12200, "description": "Versatility for any gym activity, from cardio to weights.", "badge": None},
    {"id": 33, "name": "Apex Trail Runner Pro", "category": "Unisex", "price": 12500, "mrp": 15000, "description": "Durable and rugged, built for any off-road adventure.", "badge": "Bestseller"},
    {"id": 34, "name": "Solar Boost Elite", "category": "Men", "price": 13500, "mrp": 16000, "description": "High-energy return with a carbon-fiber plate.", "badge": None},
    {"id": 35, "name": "Aura High-Fashion", "category": "Women", "price": 15000, "mrp": 18000, "description": "A designer collaboration sneaker with a runway-ready look.", "badge": "Limited Edition"},
    {"id": 36, "name": "Forge Weightlifting", "category": "Unisex", "price": 12200, "mrp": 14500, "description": "A flat, stable sole provides the perfect platform for heavy lifting.", "badge": None},
    {"id": 37, "name": "Cryo Winter Boot", "category": "Men", "price": 14800, "mrp": 17500, "description": "Insulated and waterproof to keep your feet warm and dry.", "badge": None},
    {"id": 38, "name": "Celeste Leather Sandal", "category": "Women", "price": 12100, "mrp": 14000, "description": "An elegant leather sandal for warm-weather events.", "badge": "New Arrival"},
    {"id": 39, "name": "Hyper Jump Pro", "category": "Unisex", "price": 13800, "mrp": 16500, "description": "A basketball shoe with explosive cushioning for maximum vertical leap.", "badge": "Bestseller"},
    {"id": 40, "name": "Equinox Oxford", "category": "Men", "price": 14000, "mrp": 17000, "description": "A premium dress shoe crafted from the finest full-grain leather.", "badge": None},
    {"id": 41, "name": "Diamond Heel", "category": "Women", "price": 16000, "mrp": 19000, "description": "A stunning high heel for formal occasions, adorned with subtle crystals.", "badge": "Limited Edition"},
    {"id": 42, "name": "Summit Explorer", "category": "Unisex", "price": 15500, "mrp": 18500, "description": "A professional-grade mountaineering boot for serious expeditions.", "badge": None},
    {"id": 43, "name": "Radiant Runner", "category": "Women", "price": 9300, "mrp": 11200, "description": "A bright and responsive shoe that makes every run feel effortless.", "badge": "New Arrival"},
    {"id": 44, "name": "Colossus Work Boot", "category": "Men", "price": 15200, "mrp": 18000, "description": "Steel-toed and built to withstand the toughest job sites.", "badge": None},
    {"id": 45, "name": "Simple Step Eco", "category": "Unisex", "price": 6200, "mrp": 7500, "description": "A minimalist sneaker made from recycled and sustainable materials.", "badge": "Sustainable"},
    {"id": 46, "name": "Empress Evening Heel", "category": "Women", "price": 14500, "mrp": 17500, "description": "An elegant heel designed for comfort and style during formal events.", "badge": "Limited Edition"},
    {"id": 47, "name": "Dynamic Dash", "category": "Men", "price": 8400, "mrp": 10000, "description": "Built for agility and quick movements, ideal for court sports.", "badge": None},
    {"id": 48, "name": "Zenith Pro Hiker", "category": "Unisex", "price": 16500, "mrp": 19500, "description": "Our most advanced hiking boot, ready for any professional expedition.", "badge": "Bestseller"},
    {"id": 49, "name": "Breeze Comfort Sandal", "category": "Women", "price": 6600, "mrp": 7900, "description": "Lightweight and supportive, this is your perfect summer sandal.", "badge": None},
    {"id": 50, "name": "Vector Cross-Trainer II", "category": "Men", "price": 11800, "mrp": 14000, "description": "The next generation of our all-around gym shoe, with enhanced stability.", "badge": "New Arrival"},
]


def setup_database():
    """
    Drops all tables, recreates them using raw SQL, and populates the 'products' table.
    This is DESTRUCTIVE and will reset your database.
    """
    conn = None
    try:
        print("Connecting to the database...")
        conn = get_db_connection()
        with conn.cursor() as cur:
            # --- Drop existing tables in reverse order of creation due to foreign keys ---
            print("Dropping all database tables...")
            cur.execute("DROP TABLE IF EXISTS wishlist, order_items, orders, users, products CASCADE;")

            # --- Create all tables with proper schemas and constraints ---
            print("Creating all database tables...")

            # Users Table
            cur.execute('''
                CREATE TABLE users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL
                );
            ''')

            # Products Table
            cur.execute('''
                CREATE TABLE products (
                    id INT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    category VARCHAR(50),
                    price NUMERIC(10, 2) NOT NULL,
                    mrp NUMERIC(10, 2),
                    description TEXT,
                    style_code VARCHAR(50),
                    origin VARCHAR(100),
                    image_main VARCHAR(255),
                    image_thumb1 VARCHAR(255),
                    image_thumb2 VARCHAR(255),
                    image_thumb3 VARCHAR(255),
                    image_thumb4 VARCHAR(255),
                    badge VARCHAR(50),
                    colors_available INT DEFAULT 1
                );
            ''')

            # Orders Table
            cur.execute('''
                CREATE TABLE orders (
                    id SERIAL PRIMARY KEY,
                    user_id INT REFERENCES users(id),
                    order_date TIMESTAMP NOT NULL,
                    total_amount NUMERIC(10, 2),
                    status VARCHAR(50),
                    customer_name VARCHAR(255),
                    shipping_address TEXT,
                    city VARCHAR(100),
                    postal_code VARCHAR(20),
                    payment_method VARCHAR(50)
                );
            ''')

            # Order Items Table
            cur.execute('''
                CREATE TABLE order_items (
                    id SERIAL PRIMARY KEY,
                    order_id INT REFERENCES orders(id) ON DELETE CASCADE,
                    product_id INT REFERENCES products(id),
                    product_name VARCHAR(255),
                    product_price NUMERIC(10, 2),
                    quantity INT,
                    size VARCHAR(50),
                    image VARCHAR(255)
                );
            ''')

            # Wishlist Table
            cur.execute('''
                CREATE TABLE wishlist (
                    id SERIAL PRIMARY KEY,
                    user_id INT REFERENCES users(id) ON DELETE CASCADE,
                    product_id INT REFERENCES products(id) ON DELETE CASCADE,
                    UNIQUE (user_id, product_id)
                );
            ''')
            print("All tables created successfully.")

            # --- Seed the products table using the data list ---
            print("Seeding the products table...")
            insert_query = """
                INSERT INTO products (
                    id, name, category, price, mrp, description, style_code,
                    origin, image_main, image_thumb1, image_thumb2, image_thumb3,
                    image_thumb4, badge, colors_available
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                );
            """
            for p in products_data:
                product_tuple = (
                    p.get("id"),
                    p.get("name"),
                    p.get("category"),
                    p.get("price"),
                    p.get("mrp"),
                    p.get("description"),
                    f'ALPHA-{p.get("id"):03d}',
                    'Vietnam',
                    f'{IMAGE_FOLDER_PATH}{p.get("id")}.{IMAGE_EXTENSION}',
                    f'{IMAGE_FOLDER_PATH}{p.get("id")}-thumb1.{IMAGE_EXTENSION}',
                    f'{IMAGE_FOLDER_PATH}{p.get("id")}-thumb2.{IMAGE_EXTENSION}',
                    f'{IMAGE_FOLDER_PATH}{p.get("id")}-thumb3.{IMAGE_EXTENSION}',
                    f'{IMAGE_FOLDER_PATH}{p.get("id")}-thumb4.{IMAGE_EXTENSION}',
                    p.get("badge"),
                    p.get("colors_available", 1)
                )
                cur.execute(insert_query, product_tuple)
            
            print(f"Inserted {len(products_data)} products into the database.")

            # Commit all changes to the database
            conn.commit()
            print("Database seeding and population complete.")

    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error during database setup: {error}")
        if conn:
            conn.rollback() # Roll back any partial changes
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")


# This allows you to run 'python create_db.py' from your terminal
if __name__ == '__main__':
    setup_database()
    