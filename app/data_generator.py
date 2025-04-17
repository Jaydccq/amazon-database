import csv
import os
import random
import string
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from faker import Faker

# Initialize Faker
fake = Faker()

# Configuration
NUM_USERS = 100
NUM_SELLERS = 30
NUM_CATEGORIES = 10
NUM_PRODUCTS = 100
NUM_INVENTORY_ITEMS = 150
NUM_REVIEWS = 80
NUM_CARTS = 40
NUM_CART_ITEMS = 80
NUM_ORDERS = 50
NUM_ORDER_ITEMS = 100

# Ensure output directory exists
os.makedirs('app/db/data/generated', exist_ok=True)


# Helper functions
def random_date(start_date, end_date):
    """Generate a random datetime between start_date and end_date"""
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_days = random.randrange(days_between_dates)
    return start_date + timedelta(days=random_days)


def generate_product_name():
    """Generate a realistic product name"""
    adjectives = ['Premium', 'Deluxe', 'Professional', 'Organic', 'Smart', 'Vintage']
    products = ['Headphones', 'Smartphone', 'Laptop', 'Watch', 'Camera', 'Speaker']
    return f"{random.choice(adjectives)} {random.choice(products)}"



def generate_users():
    """Generate user data"""
    users = []

    for i in range(NUM_USERS):
        user_id = i
        email = fake.email()
        # Generate separate first_name and last_name instead of fullname
        first_name = fake.first_name()
        last_name = fake.last_name()
        address = fake.address().replace('\n', ', ')
        password = generate_password_hash('test123')
        current_balance = round(random.uniform(0.0, 1000.0), 2)
        is_seller = True if i < NUM_SELLERS else False
        created_at = datetime.now()
        updated_at = datetime.now()


        users.append([
            user_id, email, password, first_name, last_name, address,
            current_balance, is_seller, created_at, updated_at
        ])

    # Write to CSV with correct column headers
    with open('app/db/data/generated/Accounts.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['user_id', 'email', 'password', 'first_name', 'last_name',
                         'address', 'current_balance', 'is_seller',
                         'created_at', 'updated_at'])
        writer.writerows(users)

    return users

def generate_categories():
    """Generate product categories"""
    categories = [
        'Electronics',
        'Clothing',
        'Home & Kitchen',
        'Books',
        'Toys & Games',
        'Beauty & Personal Care',
        'Sports & Outdoors',
        'Automotive',
        'Health & Household',
        'Grocery'
    ]

    # Write to CSV
    with open('app/db/data/generated/Products_Categories.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['category_id', 'category_name', 'created_at'])
        for i, name in enumerate(categories[:NUM_CATEGORIES]):
            created_at = datetime.now()
            writer.writerow([i, name, created_at])

    return categories[:NUM_CATEGORIES]


def generate_products(categories, users):
    """Generate product data"""
    products = []
    seller_ids = [user[0] for user in users if user[6]]  # Get IDs of users who are sellers

    for i in range(NUM_PRODUCTS):
        product_id = i
        category_id = random.randint(0, len(categories) - 1)
        product_name = generate_product_name()
        description = fake.paragraph()
        image = f"product_{i}.jpg"
        owner_id = random.choice(seller_ids)
        created_at = datetime.now()
        updated_at = datetime.now()

        products.append([
            product_id, category_id, product_name, description, image,
            owner_id, created_at, updated_at
        ])

    # Write to CSV
    with open('app/db/data/generated/Products.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['product_id', 'category_id', 'product_name', 'description',
                         'image', 'owner_id', 'created_at', 'updated_at'])
        writer.writerows(products)

    return products


def generate_inventory(products, users):
    """Generate inventory data"""
    inventory = []
    seller_ids = [user[0] for user in users if user[6]]  # Get IDs of users who are sellers

    # Keep track of seller-product pairs to ensure uniqueness
    seller_product_pairs = set()

    for i in range(NUM_INVENTORY_ITEMS):
        inventory_id = i

        # Ensure seller-product pair is unique
        while True:
            seller_id = random.choice(seller_ids)
            product_id = random.randint(0, NUM_PRODUCTS - 1)

            if (seller_id, product_id) not in seller_product_pairs:
                seller_product_pairs.add((seller_id, product_id))
                break

        quantity = random.randint(0, 100)
        unit_price = round(random.uniform(0.99, 999.99), 2)
        created_at = datetime.now()
        updated_at = datetime.now()

        inventory.append([
            inventory_id, seller_id, product_id, quantity, unit_price,
            created_at, updated_at
        ])

    # Write to CSV
    with open('app/db/data/generated/Inventory.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['inventory_id', 'seller_id', 'product_id', 'quantity',
                         'unit_price', 'created_at', 'updated_at'])
        writer.writerows(inventory)

    return inventory


def generate_reviews(products, users):
    """Generate review data"""
    reviews = []

    # Track user-product and user-seller pairs for uniqueness
    user_product_pairs = set()
    user_seller_pairs = set()

    for i in range(NUM_REVIEWS):
        review_id = i
        user_id = random.randint(0, NUM_USERS - 1)
        comment = fake.paragraph()
        review_date = datetime.now()
        updated_at = datetime.now()

        # Decide if it's a product review or seller review
        if random.random() < 0.7:  # 70% product reviews, 30% seller reviews
            # Ensure user-product pair is unique
            while True:
                product_id = random.randint(0, NUM_PRODUCTS - 1)
                if (user_id, product_id) not in user_product_pairs:
                    user_product_pairs.add((user_id, product_id))
                    break
            seller_id = None
        else:
            # Ensure user-seller pair is unique
            while True:
                seller_id = random.randint(0, NUM_SELLERS - 1)
                if (user_id, seller_id) not in user_seller_pairs:
                    user_seller_pairs.add((user_id, seller_id))
                    break
            product_id = None

        rating = random.randint(1, 5)

        reviews.append([
            review_id, user_id, comment, review_date, product_id,
            seller_id, rating, updated_at
        ])

    # Write to CSV
    with open('app/db/data/generated/Reviews_Feedbacks.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['review_id', 'user_id', 'comment', 'review_date',
                         'product_id', 'seller_id', 'rating', 'updated_at'])
        writer.writerows(reviews)

    return reviews


def generate_carts(users):
    """Generate cart data"""
    carts = []

    # Track user_ids to ensure uniqueness
    user_ids = set()

    for i in range(min(NUM_CARTS, NUM_USERS)):  # Ensure we don't exceed number of users
        cart_id = i

        # Ensure user_id is unique
        while True:
            user_id = random.randint(0, NUM_USERS - 1)
            if user_id not in user_ids:
                user_ids.add(user_id)
                break

        created_at = datetime.now()
        updated_at = datetime.now()

        carts.append([cart_id, user_id, created_at, updated_at])

    # Write to CSV
    with open('app/db/data/generated/Carts.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['cart_id', 'user_id', 'created_at', 'updated_at'])
        writer.writerows(carts)

    return carts


def generate_cart_products(carts, inventory):
    """Generate cart items data"""
    cart_products = []

    # Track cart-product-seller combinations for uniqueness
    combinations = set()

    for i in range(NUM_CART_ITEMS):
        # Ensure all references are valid
        while True:
            if not carts:  # No carts available
                break

            cart_id = random.choice(carts)[0]
            inventory_item = random.choice(inventory)
            product_id = inventory_item[2]
            seller_id = inventory_item[1]

            # Ensure combination is unique
            if (cart_id, product_id, seller_id) not in combinations:
                combinations.add((cart_id, product_id, seller_id))
                break

        quantity = random.randint(1, 5)
        price_at_addition = round(random.uniform(0.99, 499.99), 2)
        added_at = datetime.now()

        cart_products.append([
            cart_id, product_id, seller_id, quantity, price_at_addition, added_at
        ])

    # Write to CSV
    with open('app/db/data/generated/Cart_Products.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['cart_id', 'product_id', 'seller_id', 'quantity',
                         'price_at_addition', 'added_at'])
        writer.writerows(cart_products)

    return cart_products


def generate_orders(users):
    """Generate order data"""
    orders = []

    for i in range(NUM_ORDERS):
        order_id = i
        buyer_id = random.randint(0, NUM_USERS - 1)
        total_amount = round(random.uniform(10.0, 1000.0), 2)
        order_date = datetime.now()
        num_products = random.randint(1, 10)

        order_status = 'Fulfilled' if random.random() < 0.7 else 'Unfulfilled'

        orders.append([
            order_id, buyer_id, total_amount, order_date, num_products, order_status
        ])

    # Write to CSV
    with open('app/db/data/generated/Orders.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['order_id', 'buyer_id', 'total_amount', 'order_date',
                         'num_products', 'order_status'])
        writer.writerows(orders)

    return orders


def generate_order_products(orders, inventory):
    """Generate order items data"""
    order_products = []

    # Track to ensure uniqueness of composite key (order_id, product_id, seller_id)
    combinations = set()

    for i in range(NUM_ORDER_ITEMS):
        # Ensure all references are valid
        while True:
            if not orders:  # No orders available
                break

            order_id = random.choice(orders)[0]
            inventory_item = random.choice(inventory)
            product_id = inventory_item[2]
            seller_id = inventory_item[1]

            # Ensure composite key is unique
            if (order_id, product_id, seller_id) not in combinations:
                combinations.add((order_id, product_id, seller_id))
                break

        quantity = random.randint(1, 5)
        price = round(random.uniform(0.99, 499.99), 2)

        order_status = next((o[5] for o in orders if o[0] == order_id), 'Unfulfilled')
        status = 'Fulfilled' if order_status == 'Fulfilled' else 'Unfulfilled'
        fulfillment_date = datetime.now() if status == 'Fulfilled' else None

        order_products.append([
            order_id, product_id, quantity, price, seller_id, status, fulfillment_date
        ])

    # Write to CSV
    with open('app/db/data/generated/Orders_Products.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['order_id', 'product_id', 'quantity', 'price',
                         'seller_id', 'status', 'fulfillment_date'])
        writer.writerows(order_products)

    return order_products


# Main execution function
def generate_all_data():
    """Generate all data for the database"""
    print("Generating users...")
    users = generate_users()

    print("Generating categories...")
    categories = generate_categories()

    print("Generating products...")
    products = generate_products(categories, users)

    print("Generating inventory...")
    inventory = generate_inventory(products, users)

    print("Generating reviews...")
    reviews = generate_reviews(products, users)

    print("Generating carts...")
    carts = generate_carts(users)

    print("Generating cart products...")
    cart_products = generate_cart_products(carts, inventory)

    print("Generating orders...")
    orders = generate_orders(users)

    print("Generating order products...")
    order_products = generate_order_products(orders, inventory)

    print("Data generation complete! CSV files have been saved to app/db/data/generated/")
    print("Next step: Run the loading script to import data into your database.")


if __name__ == "__main__":
    generate_all_data()