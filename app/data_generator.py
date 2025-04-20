import csv
import os
import random
import string
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from faker import Faker
from collections import defaultdict

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

os.makedirs('app/db/data/generated', exist_ok=True)


def random_date(start_date, end_date):
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_days = random.randrange(days_between_dates)
    return start_date + timedelta(days=random_days)


def generate_product_name():
    adjectives = ['Premium', 'Deluxe', 'Professional', 'Organic', 'Smart', 'Vintage',
                  'Handcrafted', 'Modern', 'Classic', 'Ultra', 'Eco-Friendly', 'Portable']
    products = ['Headphones', 'Smartphone', 'Laptop', 'Watch', 'Camera', 'Speaker',
                'Tablet', 'Monitor', 'Keyboard', 'Mouse', 'Charger', 'Drone']
    return f"{random.choice(adjectives)} {random.choice(products)}"


def generate_users():
    users = []

    for i in range(NUM_USERS):
        user_id = i
        email = fake.unique.email()
        first_name = fake.first_name()
        last_name = fake.last_name()
        address = fake.address().replace('\n', ', ')
        password = generate_password_hash('test123')
        current_balance = round(random.uniform(1000.0, 5000.0), 2)
        is_seller = True if i < NUM_SELLERS else False
        created_at = random_date(datetime.now() - timedelta(days=365), datetime.now())
        updated_at = random_date(created_at, datetime.now())

        users.append([
            user_id, email, password, first_name, last_name, address,
            current_balance, is_seller, created_at, updated_at
        ])

    with open('app/db/data/generated/Accounts.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['user_id', 'email', 'password', 'first_name', 'last_name',
                         'address', 'current_balance', 'is_seller',
                         'created_at', 'updated_at'])
        writer.writerows(users)

    return users


def generate_categories():
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
        'Grocery',
        'Office Products',
        'Garden & Outdoor',
        'Pet Supplies',
        'Baby',
        'Tools & Home Improvement',
        'Arts, Crafts & Sewing',
        'Video Games',
        'Movies & TV',
        'Musical Instruments',
        'Industrial & Scientific'
    ]

    with open('app/db/data/generated/Products_Categories.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['category_id', 'category_name', 'created_at'])
        for i, name in enumerate(categories[:NUM_CATEGORIES]):
            created_at = random_date(datetime.now() - timedelta(days=365), datetime.now())
            writer.writerow([i, name, created_at])

    return categories[:NUM_CATEGORIES]


def generate_products(categories, users):
    products = []
    seller_ids = [user[0] for user in users if user[7]]

    for i in range(NUM_PRODUCTS):
        product_id = i
        category_id = random.randint(0, len(categories) - 1)
        product_name = generate_product_name()
        description = ' '.join(fake.paragraphs(nb=random.randint(1, 2)))
        image = f"product_{i}.jpg"
        owner_id = random.choice(seller_ids)
        created_at = random_date(datetime.now() - timedelta(days=365), datetime.now())
        updated_at = random_date(created_at, datetime.now())

        products.append([
            product_id, category_id, product_name, description, image,
            owner_id, created_at, updated_at
        ])

    with open('app/db/data/generated/Products.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['product_id', 'category_id', 'product_name', 'description',
                         'image', 'owner_id', 'created_at', 'updated_at'])
        writer.writerows(products)

    return products


def generate_inventory(products, users):
    inventory = []
    seller_ids = [user[0] for user in users if user[7]]

    seller_product_pairs = set()

    for product in products:
        product_id = product[0]
        owner_id = product[5]

        num_sellers = random.randint(1, min(5, len(seller_ids)))

        available_sellers = seller_ids.copy()
        if owner_id in available_sellers:
            available_sellers.remove(owner_id)


        selected_sellers = random.sample(available_sellers, min(num_sellers - 1, len(available_sellers)))

        if owner_id in seller_ids:
            selected_sellers.append(owner_id)

        for seller_id in selected_sellers:
            if (seller_id, product_id) not in seller_product_pairs:
                seller_product_pairs.add((seller_id, product_id))

                inventory_id = len(inventory)
                quantity = random.randint(50, 500)
                unit_price = round(random.uniform(0.99, 999.99), 2)
                created_at = random_date(datetime.now() - timedelta(days=365), datetime.now())
                updated_at = random_date(created_at, datetime.now())

                inventory.append([
                    inventory_id, seller_id, product_id, quantity, unit_price,
                    created_at, updated_at, owner_id
                ])

    current_inventory_count = len(inventory)
    while len(inventory) < NUM_INVENTORY_ITEMS and len(seller_product_pairs) < len(seller_ids) * len(products):
        product_id = random.randint(0, NUM_PRODUCTS - 1)
        seller_id = random.choice(seller_ids)

        owner_id = next((p[5] for p in products if p[0] == product_id), None)
        if not owner_id:
            continue

        if (seller_id, product_id) not in seller_product_pairs:
            seller_product_pairs.add((seller_id, product_id))

            inventory_id = len(inventory)
            quantity = random.randint(50, 500)
            unit_price = round(random.uniform(0.99, 999.99), 2)
            created_at = random_date(datetime.now() - timedelta(days=365), datetime.now())
            updated_at = random_date(created_at, datetime.now())

            inventory.append([
                inventory_id, seller_id, product_id, quantity, unit_price,
                created_at, updated_at, owner_id
            ])

    with open('app/db/data/generated/Inventory.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['inventory_id', 'seller_id', 'product_id', 'quantity',
                         'unit_price', 'created_at', 'updated_at', 'owner_id'])
        writer.writerows(inventory)

    return inventory


def generate_reviews(products, users):
    reviews = []

    if not products or not users:
        return reviews

    user_product_pairs = set()
    user_seller_pairs = set()

    valid_user_ids = [user[0] for user in users]
    valid_seller_ids = [user[0] for user in users if user[7]]
    valid_product_ids = [product[0] for product in products]

    for product_id in valid_product_ids:
        num_reviews = random.randint(10, 15)

        for _ in range(num_reviews):
            attempts = 0
            user_id = None
            while attempts < 50:
                temp_user_id = random.choice(valid_user_ids)
                if (temp_user_id, product_id) not in user_product_pairs:
                    user_id = temp_user_id
                    user_product_pairs.add((user_id, product_id))
                    break
                attempts += 1

            if user_id is None:
                continue

            rating_weights = [0.10, 0.15, 0.20, 0.30, 0.25]
            rating = random.choices([1, 2, 3, 4, 5], weights=rating_weights)[0]

            comment = ' '.join(fake.paragraphs(nb=1))
            review_date = random_date(datetime.now() - timedelta(days=180), datetime.now())
            updated_at = random_date(review_date, datetime.now())

            review_id = len(reviews)
            reviews.append([
                review_id, user_id, comment, review_date, product_id,
                None, rating, updated_at
            ])

    num_seller_reviews = min(NUM_REVIEWS - len(reviews), len(valid_seller_ids) * 5)

    for _ in range(num_seller_reviews):
        attempts = 0
        seller_id = None
        user_id = None

        while attempts < 50:
            temp_user_id = random.choice(valid_user_ids)
            temp_seller_id = random.choice(valid_seller_ids)
            if (temp_user_id, temp_seller_id) not in user_seller_pairs and temp_user_id != temp_seller_id:
                user_id = temp_user_id
                seller_id = temp_seller_id
                user_seller_pairs.add((user_id, seller_id))
                break
            attempts += 1

        if seller_id is None or user_id is None:
            continue

        rating_weights = [0.08, 0.12, 0.20, 0.35, 0.25]
        rating = random.choices([1, 2, 3, 4, 5], weights=rating_weights)[0]

        comment = ' '.join(fake.paragraphs(nb=1))
        review_date = random_date(datetime.now() - timedelta(days=180), datetime.now())
        updated_at = random_date(review_date, datetime.now())

        review_id = len(reviews)
        reviews.append([
            review_id, user_id, comment, review_date, None,
            seller_id, rating, updated_at
        ])

    with open('app/db/data/generated/Reviews_Feedbacks.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['review_id', 'user_id', 'comment', 'review_date',
                         'product_id', 'seller_id', 'rating', 'updated_at'])
        writer.writerows(reviews)

    return reviews


def generate_carts(users):
    carts = []

    valid_user_ids = [user[0] for user in users]

    max_carts = min(NUM_CARTS, len(valid_user_ids))

    user_ids = set()

    for i in range(max_carts):
        cart_id = i

        attempts = 0
        user_id = None

        while attempts < 50:
            temp_user_id = random.choice(valid_user_ids)
            if temp_user_id not in user_ids:
                user_id = temp_user_id
                user_ids.add(user_id)
                break
            attempts += 1

        if user_id is None:
            continue

        created_at = random_date(datetime.now() - timedelta(days=30), datetime.now())
        updated_at = random_date(created_at, datetime.now())

        carts.append([cart_id, user_id, created_at, updated_at])

    with open('app/db/data/generated/Carts.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['cart_id', 'user_id', 'created_at', 'updated_at'])
        writer.writerows(carts)

    return carts


def generate_cart_products(carts, inventory):
    cart_products = []

    if not carts or not inventory:
        return cart_products

    valid_cart_ids = [cart[0] for cart in carts]

    combinations = set()

    max_cart_items = min(NUM_CART_ITEMS, len(valid_cart_ids) * len(inventory))

    for i in range(max_cart_items):
        attempts = 0
        cart_id = None
        product_id = None
        seller_id = None

        while attempts < 50:
            temp_cart_id = random.choice(valid_cart_ids)
            temp_inventory_item = random.choice(inventory)
            temp_product_id = temp_inventory_item[2]
            temp_seller_id = temp_inventory_item[1]

            if (temp_cart_id, temp_product_id, temp_seller_id) not in combinations:
                cart_id = temp_cart_id
                product_id = temp_product_id
                seller_id = temp_seller_id
                combinations.add((cart_id, product_id, seller_id))
                break
            attempts += 1

        if cart_id is None or product_id is None or seller_id is None:
            continue

        quantity = random.randint(1, 5)
        price_at_addition = round(random.uniform(0.99, 499.99), 2)
        added_at = random_date(datetime.now() - timedelta(days=7), datetime.now())

        cart_products.append([
            cart_id, product_id, seller_id, quantity, price_at_addition, added_at
        ])

    with open('app/db/data/generated/Cart_Products.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['cart_id', 'product_id', 'seller_id', 'quantity',
                         'price_at_addition', 'added_at'])
        writer.writerows(cart_products)

    return cart_products


def generate_orders(users):
    orders = []

    valid_user_ids = [user[0] for user in users]

    for user_id in valid_user_ids:
        num_orders = random.randint(10, 15)

        for _ in range(num_orders):
            order_id = len(orders)
            total_amount = round(random.uniform(10.0, 1000.0), 2)
            order_date = random_date(datetime.now() - timedelta(days=365), datetime.now())
            num_products = random.randint(1, 5)
            order_status = 'Fulfilled' if random.random() < 0.8 else 'Unfulfilled'

            orders.append([
                order_id, user_id, total_amount, order_date, num_products, order_status
            ])

            if len(orders) >= NUM_ORDERS:
                break

        if len(orders) >= NUM_ORDERS:
            break

    with open('app/db/data/generated/Orders.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['order_id', 'buyer_id', 'total_amount', 'order_date',
                         'num_products', 'order_status'])
        writer.writerows(orders)

    return orders


def generate_order_products(orders, inventory):
    order_products = []

    if not orders or not inventory:
        return order_products

    order_item_count = defaultdict(int)

    combinations = set()

    for order in orders:
        order_id = order[0]

        num_items = random.randint(1, 5)
        for _ in range(num_items):
            attempts = 0
            added = False

            while attempts < 20 and not added:  # Limit attempts
                inventory_item = random.choice(inventory)
                product_id = inventory_item[2]
                seller_id = inventory_item[1]

                if (order_id, product_id, seller_id) not in combinations:
                    combinations.add((order_id, product_id, seller_id))

                    quantity = random.randint(1, 3)
                    price = round(random.uniform(0.99, 499.99), 2)

                    order_status = order[5]
                    status = 'Fulfilled' if order_status == 'Fulfilled' else 'Unfulfilled'
                    fulfillment_date = datetime.now() if status == 'Fulfilled' else None

                    order_products.append([
                        order_id, product_id, quantity, price, seller_id, status, fulfillment_date
                    ])

                    order_item_count[order_id] += 1
                    added = True

                attempts += 1

    remaining_items = NUM_ORDER_ITEMS - len(order_products)
    if remaining_items > 0:
        order_priority = sorted(orders, key=lambda o: order_item_count[o[0]])

        for _ in range(remaining_items):
            if not order_priority:
                break

            order = order_priority.pop(0)
            order_id = order[0]

            attempts = 0
            added = False

            while attempts < 20 and not added:
                inventory_item = random.choice(inventory)
                product_id = inventory_item[2]
                seller_id = inventory_item[1]

                if (order_id, product_id, seller_id) not in combinations:
                    combinations.add((order_id, product_id, seller_id))

                    quantity = random.randint(1, 3)
                    price = round(random.uniform(0.99, 499.99), 2)

                    order_status = order[5]
                    status = 'Fulfilled' if order_status == 'Fulfilled' else 'Unfulfilled'
                    fulfillment_date = datetime.now() if status == 'Fulfilled' else None

                    order_products.append([
                        order_id, product_id, quantity, price, seller_id, status, fulfillment_date
                    ])

                    order_item_count[order_id] += 1
                    added = True

                attempts += 1

            if added:
                order_priority.append(order)
                order_priority.sort(key=lambda o: order_item_count[o[0]])

            if len(order_products) >= NUM_ORDER_ITEMS:
                break

    with open('app/db/data/generated/Orders_Products.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['order_id', 'product_id', 'quantity', 'price',
                         'seller_id', 'status', 'fulfillment_date'])
        writer.writerows(order_products)

    return order_products


def generate_all_data():
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
    print(f"Generated {len(users)} users, {len(products)} products, {len(inventory)} inventory items")
    print(f"{len(reviews)} reviews, {len(orders)} orders, and {len(order_products)} order items")
    print("Next step: Run the loading script to import data into your database.")


if __name__ == "__main__":
    generate_all_data()