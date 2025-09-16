
# add_wishlist_table.py
import sqlite3

DB_FILE = 'products.db'

print(f"Connecting to database: {DB_FILE}")
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

print("Creating the 'wishlist' table if it doesn't exist...")
# This command will only create the table if it's missing.
# If it already exists, it will do nothing and not cause an error.
c.execute('''
CREATE TABLE IF NOT EXISTS wishlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (product_id) REFERENCES products (id),
    UNIQUE(user_id, product_id)
)
''')

conn.commit()
conn.close()

print("Database updated successfully. The 'wishlist' table is ready.")
