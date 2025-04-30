import csv
import os
import random
import string
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from faker import Faker
from collections import defaultdict

# --- Configuration Constants ---
fake = Faker()
fake.unique.clear()
NUM_USERS = 200
NUM_SELLERS = 50
NUM_CATEGORIES = 20
NUM_PRODUCTS = 300
AVG_SELLERS_PER_PRODUCT = 3
NUM_INVENTORY_ITEMS = NUM_PRODUCTS * AVG_SELLERS_PER_PRODUCT
NUM_REVIEWS = 5000
NUM_CARTS = 100
NUM_CART_ITEMS = 200
NUM_ORDERS = 3000
NUM_ORDER_ITEMS = 8000
OUTPUT_DIR = 'app/db/data/generated' # Directory for generated CSVs

# --- Helper Functions ---
def random_date(start_date, end_date):
    """Generates random date within range."""
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_days = random.randrange(days_between_dates)
    return start_date + timedelta(days=random_days)

# Updated function for better product names
def generate_product_name():
    """Creates more diverse random product names."""
    adjectives = [
        'Premium', 'Deluxe', 'Professional', 'Organic', 'Smart', 'Vintage', 'Handcrafted',
        'Modern', 'Classic', 'Ultra', 'Eco-Friendly', 'Portable', 'Wireless', 'Heavy-Duty',
        'Compact', 'Ergonomic', 'Waterproof', 'Bluetooth', 'Solar-Powered', 'AI-Enhanced',
        'Artisan', 'Gourmet', 'Stealth', 'Tactical', 'Miniature', 'Industrial', 'Luxury',
        'Sustainable', 'Recycled', 'Hypoallergenic'
    ]
    nouns = [
        'Headphones', 'Smartphone', 'Laptop', 'Watch', 'Camera', 'Speaker', 'Tablet', 'Monitor',
        'Keyboard', 'Mouse', 'Charger', 'Drone', 'Backpack', 'Water Bottle', 'Coffee Maker',
        'Desk Lamp', 'Router', 'Gaming Console', 'Projector', 'Air Purifier', 'Blender',
        'Electric Toothbrush', 'Fitness Tracker', 'Security Camera', 'Smart Lock', 'Thermostat',
        'Cookware Set', 'Cutlery Set', 'Robot Vacuum', 'Power Bank'
    ]
    features = ['', 'Pro', 'Max', 'Mini', 'Air', 'Plus', 'Elite', 'X', 'Z', 'Series II', 'Gen 3']
    materials = ['', 'Wood', 'Steel', 'Titanium', 'Carbon Fiber', 'Bamboo', 'Glass', 'Leather']

    name_parts = [random.choice(adjectives), random.choice(nouns)]
    if random.random() < 0.3: name_parts.insert(1, random.choice(materials))
    if random.random() < 0.5: name_parts.append(random.choice(features))

    return ' '.join(part for part in name_parts if part)


# --- Data Generation Functions ---
def generate_users():
    """Generates user account data."""
    users = []
    for i in range(NUM_USERS):
        user_id = i
        email = fake.unique.email()
        first_name = fake.first_name()
        last_name = fake.last_name()
        address = fake.address().replace('\n', ', ')
        password = generate_password_hash('test123') # Hash default password
        current_balance = round(random.uniform(1000.0, 5000.0), 2)
        is_seller = i < NUM_SELLERS # First N users are sellers
        created_at = random_date(datetime.now() - timedelta(days=365), datetime.now())
        updated_at = random_date(created_at, datetime.now())
        users.append([
            user_id, email, password, first_name, last_name, address,
            current_balance, is_seller, created_at, updated_at
        ])

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, 'Accounts.csv')
    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['user_id', 'email', 'password', 'first_name', 'last_name',
                         'address', 'current_balance', 'is_seller',
                         'created_at', 'updated_at'])
        writer.writerows(users)
    return users

def generate_categories():
    """Generates product category data."""
    categories = [
        'Electronics', 'Clothing', 'Home & Kitchen', 'Books', 'Toys & Games',
        'Beauty & Personal Care', 'Sports & Outdoors', 'Automotive', 'Health & Household', 'Grocery',
        'Office Products', 'Garden & Outdoor', 'Pet Supplies', 'Baby', 'Tools & Home Improvement',
        'Arts, Crafts & Sewing', 'Video Games', 'Movies & TV', 'Musical Instruments', 'Industrial & Scientific'
    ]
    categories_to_write = []
    for i, name in enumerate(categories[:NUM_CATEGORIES]):
        created_at = random_date(datetime.now() - timedelta(days=365), datetime.now())
        categories_to_write.append([i, name, created_at])

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, 'Products_Categories.csv')
    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['category_id', 'category_name', 'created_at'])
        writer.writerows(categories_to_write)
    return categories[:NUM_CATEGORIES]

# Updated function to ensure unique product names
def generate_products(categories, users):
    """Generates product catalog data ensuring unique names."""
    products = []
    seller_ids = [user[0] for user in users if user[7]]
    if not seller_ids:
        print("Warning: No sellers found.")
        return []

    used_product_names = set() # Keep track of generated names

    for i in range(NUM_PRODUCTS):
        product_id = i
        category_id = random.randint(0, min(len(categories), NUM_CATEGORIES) - 1)

        # --- Generate Unique Product Name ---
        base_name = generate_product_name()
        product_name = base_name
        counter = 1
        while product_name in used_product_names: # Check for duplicates
            product_name = f"{base_name} #{counter}" # Append counter if duplicate
            counter += 1
        used_product_names.add(product_name) # Add final unique name to set
        # --- End Unique Name Generation ---

        description = ' '.join(fake.paragraphs(nb=random.randint(1, 2)))
        image = f"product_{i}.jpg"
        owner_id = random.choice(seller_ids)
        created_at = random_date(datetime.now() - timedelta(days=365), datetime.now())
        updated_at = random_date(created_at, datetime.now())
        products.append([
            product_id, category_id, product_name, description, image,
            owner_id, created_at, updated_at
        ])

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, 'Products.csv')
    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['product_id', 'category_id', 'product_name', 'description',
                         'image', 'owner_id', 'created_at', 'updated_at'])
        writer.writerows(products)
    return products

def generate_inventory(products, users):
    """Generates seller inventory data."""
    inventory = []
    seller_ids = [user[0] for user in users if user[7]]
    if not seller_ids or not products:
        print("Warning: No sellers or products for inventory.")
        return []

    seller_product_pairs = set() # Ensure unique (seller, product)

    for product in products:
        product_id = product[0]
        owner_id = product[5]
        num_sellers_for_this = random.randint(1, min(5, len(seller_ids)))
        available_sellers = seller_ids.copy()
        if owner_id in available_sellers: available_sellers.remove(owner_id)
        selected_sellers = random.sample(available_sellers, min(num_sellers_for_this - 1, len(available_sellers)))
        if owner_id in seller_ids: selected_sellers.append(owner_id)

        for seller_id in selected_sellers:
            if (seller_id, product_id) not in seller_product_pairs:
                seller_product_pairs.add((seller_id, product_id))
                inventory_id = len(inventory)
                quantity = random.randint(50, 500)
                unit_price = round(random.uniform(0.99, 999.99), 2)
                created_at = random_date(datetime.now() - timedelta(days=365), datetime.now())
                updated_at = random_date(created_at, datetime.now())
                inventory.append([ inventory_id, seller_id, product_id, quantity, unit_price, created_at, updated_at, owner_id ])

    while len(inventory) < NUM_INVENTORY_ITEMS and len(seller_product_pairs) < len(seller_ids) * len(products):
        product_id = random.choice([p[0] for p in products])
        seller_id = random.choice(seller_ids)
        owner_id = next((p[5] for p in products if p[0] == product_id), None)
        if not owner_id: continue
        if (seller_id, product_id) not in seller_product_pairs:
            seller_product_pairs.add((seller_id, product_id))
            inventory_id = len(inventory)
            quantity = random.randint(50, 500)
            unit_price = round(random.uniform(0.99, 999.99), 2)
            created_at = random_date(datetime.now() - timedelta(days=365), datetime.now())
            updated_at = random_date(created_at, datetime.now())
            inventory.append([ inventory_id, seller_id, product_id, quantity, unit_price, created_at, updated_at, owner_id ])

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, 'Inventory.csv')
    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['inventory_id', 'seller_id', 'product_id', 'quantity', 'unit_price', 'created_at', 'updated_at', 'owner_id'])
        writer.writerows(inventory)
    return inventory

def generate_reviews(products, users):
    """Generates product and seller reviews."""
    reviews = []
    if not products or not users: return reviews

    user_product_pairs = set()
    user_seller_pairs = set()
    valid_user_ids = [user[0] for user in users]
    valid_seller_ids = [user[0] for user in users if user[7]]
    valid_product_ids = [product[0] for product in products]
    product_review_target = int(NUM_REVIEWS * 0.7)
    seller_review_target = NUM_REVIEWS - product_review_target

    # Product Reviews
    for _ in range(product_review_target):
        if not valid_product_ids: break
        attempts = 0; user_id, product_id = None, None
        while attempts < 50:
            temp_user_id = random.choice(valid_user_ids)
            temp_product_id = random.choice(valid_product_ids)
            if (temp_user_id, temp_product_id) not in user_product_pairs:
                user_id, product_id = temp_user_id, temp_product_id
                user_product_pairs.add((user_id, product_id)); break
            attempts += 1
        if user_id is None: continue

        rating = random.choices([1, 2, 3, 4, 5], weights=[0.10, 0.15, 0.20, 0.30, 0.25])[0]
        comment = ' '.join(fake.paragraphs(nb=1))
        review_date = random_date(datetime.now() - timedelta(days=180), datetime.now())
        updated_at = random_date(review_date, datetime.now())
        upvotes = random.randint(0, 50)   # Generate upvotes
        downvotes = random.randint(0, 10) # Generate downvotes
        review_id = len(reviews)
        reviews.append([ review_id, user_id, comment, review_date, product_id, None, rating, updated_at, upvotes, downvotes ])
        if len(reviews) >= NUM_REVIEWS: break

    # Seller Reviews
    current_seller_reviews = 0
    while len(reviews) < NUM_REVIEWS and current_seller_reviews < seller_review_target:
        if not valid_seller_ids: break
        attempts = 0; user_id, seller_id = None, None
        while attempts < 50:
            temp_user_id = random.choice(valid_user_ids)
            temp_seller_id = random.choice(valid_seller_ids)
            if temp_user_id != temp_seller_id and (temp_user_id, temp_seller_id) not in user_seller_pairs:
                user_id, seller_id = temp_user_id, temp_seller_id
                user_seller_pairs.add((user_id, seller_id)); break
            attempts += 1
        if user_id is None: continue

        rating = random.choices([1, 2, 3, 4, 5], weights=[0.08, 0.12, 0.20, 0.35, 0.25])[0]
        comment = ' '.join(fake.paragraphs(nb=1))
        review_date = random_date(datetime.now() - timedelta(days=180), datetime.now())
        updated_at = random_date(review_date, datetime.now())
        upvotes = random.randint(0, 30)   # Generate upvotes
        downvotes = random.randint(0, 8)  # Generate downvotes
        review_id = len(reviews)
        reviews.append([ review_id, user_id, comment, review_date, None, seller_id, rating, updated_at, upvotes, downvotes ])
        current_seller_reviews += 1
        if len(reviews) >= NUM_REVIEWS: break

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, 'Reviews_Feedbacks.csv')
    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['review_id', 'user_id', 'comment', 'review_date', 'product_id', 'seller_id', 'rating', 'updated_at', 'upvotes', 'downvotes'])
        writer.writerows(reviews)
    return reviews


def generate_review_votes(reviews, users):
    """Generates votes on reviews (new table)."""
    review_votes = []
    if not reviews or not users: return review_votes

    valid_user_ids = [user[0] for user in users]
    valid_review_ids = [review[0] for review in reviews]
    num_votes_to_generate = min(len(valid_user_ids) * 5, 10000)
    user_review_voted = set()

    for _ in range(num_votes_to_generate):
        attempts = 0; user_id, review_id = None, None
        while attempts < 50:
            temp_user_id = random.choice(valid_user_ids)
            temp_review_id = random.choice(valid_review_ids)
            if (temp_user_id, temp_review_id) not in user_review_voted:
                user_id, review_id = temp_user_id, temp_review_id
                user_review_voted.add((user_id, review_id)); break
            attempts += 1
        if user_id is None: continue

        vote_type = random.choice([1, -1]) # 1=upvote, -1=downvote
        voted_at = random_date(datetime.now() - timedelta(days=90), datetime.now())
        review_votes.append([ user_id, review_id, vote_type, voted_at ]) # vote_id is SERIAL

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, 'ReviewVotes.csv')
    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['user_id', 'review_id', 'vote_type', 'voted_at'])
        writer.writerows(review_votes)
    return review_votes

def generate_carts(users):
    """Generates shopping cart headers."""
    carts = []
    valid_user_ids = [user[0] for user in users]
    if not valid_user_ids: return []

    max_carts = min(NUM_CARTS, len(valid_user_ids))
    user_ids_with_cart = set()

    for i in range(max_carts):
        cart_id = i; attempts = 0; user_id = None
        while attempts < 50:
            temp_user_id = random.choice(valid_user_ids)
            if temp_user_id not in user_ids_with_cart:
                user_id = temp_user_id; user_ids_with_cart.add(user_id); break
            attempts += 1
        if user_id is None: continue

        created_at = random_date(datetime.now() - timedelta(days=30), datetime.now())
        updated_at = random_date(created_at, datetime.now())
        carts.append([cart_id, user_id, created_at, updated_at])

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, 'Carts.csv')
    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['cart_id', 'user_id', 'created_at', 'updated_at'])
        writer.writerows(carts)
    return carts

def generate_cart_products(carts, inventory):
    """Generates items within shopping carts."""
    cart_products = []
    if not carts or not inventory: return cart_products

    valid_cart_ids = [cart[0] for cart in carts]
    inventory_map = {(item[2], item[1]): item[4] for item in inventory}
    combinations = set() # Ensure unique (cart, product, seller)
    max_cart_items = min(NUM_CART_ITEMS, len(valid_cart_ids) * len(inventory))

    for _ in range(max_cart_items):
        attempts = 0; cart_id, product_id, seller_id = None, None, None; price_at_addition = None
        while attempts < 50:
            temp_cart_id = random.choice(valid_cart_ids)
            temp_inventory_item = random.choice(inventory)
            temp_product_id = temp_inventory_item[2]
            temp_seller_id = temp_inventory_item[1]
            if (temp_cart_id, temp_product_id, temp_seller_id) not in combinations:
                cart_id, product_id, seller_id = temp_cart_id, temp_product_id, temp_seller_id
                price_at_addition = inventory_map.get((product_id, seller_id), round(random.uniform(1,500),2))
                combinations.add((cart_id, product_id, seller_id)); break
            attempts += 1
        if cart_id is None: continue

        quantity = random.randint(1, 5)
        added_at = random_date(datetime.now() - timedelta(days=7), datetime.now())
        status = 'in_cart' if random.random() < 0.9 else 'saved_for_later' # Add status column
        cart_products.append([ cart_id, product_id, seller_id, quantity, price_at_addition, added_at, status ])

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, 'Cart_Products.csv')
    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['cart_id', 'product_id', 'seller_id', 'quantity', 'price_at_addition', 'added_at', 'status'])
        writer.writerows(cart_products)
    return cart_products

def generate_orders(users):
    """Generates order header data."""
    orders = []
    valid_user_ids = [user[0] for user in users]
    if not valid_user_ids: return []

    order_count = 0
    while order_count < NUM_ORDERS:
        user_id = random.choice(valid_user_ids)
        num_orders_for_user = random.randint(0, int(NUM_ORDERS/len(valid_user_ids) * 2 + 1))
        for _ in range(num_orders_for_user):
            if order_count >= NUM_ORDERS: break
            order_id = order_count
            total_amount = round(random.uniform(10.0, 1000.0), 2)
            order_date = random_date(datetime.now() - timedelta(days=365), datetime.now())
            num_products = random.randint(1, 5)
            order_status = 'Fulfilled' if random.random() < 0.8 else 'Unfulfilled'
            orders.append([ order_id, user_id, total_amount, order_date, num_products, order_status ])
            order_count += 1
        if order_count >= NUM_ORDERS: break

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, 'Orders.csv')
    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['order_id', 'buyer_id', 'total_amount', 'order_date', 'num_products', 'order_status'])
        writer.writerows(orders)
    return orders

def generate_order_products(orders, inventory):
    """Generates items within orders."""
    order_products = []
    if not orders or not inventory: return order_products

    inventory_map = {(item[2], item[1]): item[4] for item in inventory}
    order_item_count = defaultdict(int)
    combinations = set() # Ensure unique (order, product, seller)
    items_generated = 0

    for order in orders:
        order_id = order[0]; order_status = order[5]
        num_items_this_order = random.randint(1, 5)
        for _ in range(num_items_this_order):
            if items_generated >= NUM_ORDER_ITEMS: break
            attempts = 0; added = False
            while attempts < 20 and not added:
                inventory_item = random.choice(inventory)
                product_id = inventory_item[2]; seller_id = inventory_item[1]
                if (order_id, product_id, seller_id) not in combinations:
                    combinations.add((order_id, product_id, seller_id))
                    quantity = random.randint(1, 3)
                    price = inventory_map.get((product_id, seller_id), round(random.uniform(1, 500), 2))
                    status = 'Fulfilled' if order_status == 'Fulfilled' else 'Unfulfilled'
                    fulfillment_date = datetime.now() if status == 'Fulfilled' else None
                    order_products.append([ order_id, product_id, quantity, price, seller_id, status, fulfillment_date ]) # order_item_id is SERIAL
                    order_item_count[order_id] += 1; items_generated += 1; added = True
                attempts += 1
        if items_generated >= NUM_ORDER_ITEMS: break

    while items_generated < NUM_ORDER_ITEMS:
        order_priority = sorted(orders, key=lambda o: order_item_count[o[0]])
        if not order_priority: break
        order = order_priority[0]; order_id = order[0]; order_status = order[5]
        attempts = 0; added = False
        while attempts < 20 and not added:
            inventory_item = random.choice(inventory)
            product_id = inventory_item[2]; seller_id = inventory_item[1]
            if (order_id, product_id, seller_id) not in combinations:
                combinations.add((order_id, product_id, seller_id))
                quantity = random.randint(1, 3)
                price = inventory_map.get((product_id, seller_id), round(random.uniform(1, 500), 2))
                status = 'Fulfilled' if order_status == 'Fulfilled' else 'Unfulfilled'
                fulfillment_date = datetime.now() if status == 'Fulfilled' else None
                order_products.append([ order_id, product_id, quantity, price, seller_id, status, fulfillment_date ])
                order_item_count[order_id] += 1; items_generated += 1; added = True
            attempts += 1
        if not added: order_item_count[order_id] = float('inf')
        if items_generated >= NUM_ORDER_ITEMS: break

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, 'Orders_Products.csv')
    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['order_id', 'product_id', 'quantity', 'price', 'seller_id', 'status', 'fulfillment_date'])
        writer.writerows(order_products)
    return order_products

# --- Main Execution ---
def generate_all_data():
    """Runs all data generation steps."""
    print("Generating users...")
    users = generate_users()
    print("Generating categories...")
    categories = generate_categories()
    print("Generating products...")
    products = generate_products(categories, users) # Uses updated function
    print("Generating inventory...")
    inventory = generate_inventory(products, users)
    print("Generating reviews...")
    reviews = generate_reviews(products, users)
    print("Generating review votes...")
    review_votes = generate_review_votes(reviews, users)
    print("Generating carts...")
    carts = generate_carts(users)
    print("Generating cart products...")
    cart_products = generate_cart_products(carts, inventory)
    print("Generating orders...")
    orders = generate_orders(users)
    print("Generating order products...")
    order_products = generate_order_products(orders, inventory)

    print(f"\nData generation complete! CSVs saved to {OUTPUT_DIR}")
    print(f"Generated {len(users)} users, {len(products)} products, {len(inventory)} inventory items")
    print(f"{len(reviews)} reviews, {len(review_votes)} review votes, {len(orders)} orders, {len(order_products)} order items")
    print("Next: Run load.sql script.")

if __name__ == "__main__":
    # Define constants if run directly
    NUM_USERS = 200
    NUM_SELLERS = 50
    NUM_CATEGORIES = 20
    NUM_PRODUCTS = 300
    AVG_SELLERS_PER_PRODUCT = 3
    NUM_INVENTORY_ITEMS = NUM_PRODUCTS * AVG_SELLERS_PER_PRODUCT
    NUM_REVIEWS = 5000
    NUM_CARTS = 100
    NUM_CART_ITEMS = 200
    NUM_ORDERS = 3000
    NUM_ORDER_ITEMS = 8000
    OUTPUT_DIR = 'app/db/data/generated'

    generate_all_data() # Execute main generation function