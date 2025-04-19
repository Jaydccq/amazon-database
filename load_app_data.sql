
TRUNCATE TABLE orders_products CASCADE;
TRUNCATE TABLE cart_products CASCADE;
TRUNCATE TABLE reviews_feedbacks CASCADE;
TRUNCATE TABLE inventory CASCADE;
TRUNCATE TABLE carts CASCADE;
TRUNCATE TABLE orders CASCADE;
TRUNCATE TABLE products CASCADE;
TRUNCATE TABLE products_categories CASCADE;
TRUNCATE TABLE accounts CASCADE;


\copy accounts(user_id, email, password, first_name, last_name, address, current_balance, is_seller, created_at, updated_at) FROM 'app/db/data/generated/Accounts.csv' WITH (FORMAT CSV, DELIMITER ',', HEADER true);

\copy products_categories(category_id, category_name, created_at) FROM 'app/db/data/generated/Products_Categories.csv' WITH (FORMAT CSV, DELIMITER ',', HEADER true);

\copy products(product_id, category_id, product_name, description, image, owner_id, created_at, updated_at) FROM 'app/db/data/generated/Products.csv' WITH (FORMAT CSV, DELIMITER ',', HEADER true);

\copy inventory(inventory_id, seller_id, product_id, quantity, unit_price, created_at, updated_at,owner_id) FROM 'app/db/data/generated/Inventory.csv' WITH (FORMAT CSV, DELIMITER ',', HEADER true);

\copy reviews_feedbacks(review_id, user_id, comment, review_date, product_id, seller_id, rating, updated_at) FROM 'app/db/data/generated/Reviews_Feedbacks.csv' WITH (FORMAT CSV, DELIMITER ',', HEADER true);

\copy carts(cart_id, user_id, created_at, updated_at) FROM 'app/db/data/generated/Carts.csv' WITH (FORMAT CSV, DELIMITER ',', HEADER true);

\copy cart_products(cart_id, product_id, seller_id, quantity, price_at_addition, added_at) FROM 'app/db/data/generated/Cart_Products.csv' WITH (FORMAT CSV, DELIMITER ',', HEADER true);

\copy orders(order_id, buyer_id, total_amount, order_date, num_products, order_status) FROM 'app/db/data/generated/Orders.csv' WITH (FORMAT CSV, DELIMITER ',', HEADER true);

\copy orders_products(order_id, product_id, quantity, price, seller_id, status, fulfillment_date) FROM 'app/db/data/generated/Orders_Products.csv' WITH (FORMAT CSV, DELIMITER ',', HEADER true);



SELECT pg_catalog.setval('accounts_user_id_seq', COALESCE((SELECT MAX(user_id) FROM accounts), 1), true);
SELECT pg_catalog.setval('products_categories_category_id_seq', COALESCE((SELECT MAX(category_id) FROM products_categories), 1), true);
SELECT pg_catalog.setval('products_product_id_seq', COALESCE((SELECT MAX(product_id) FROM products), 1), true);
SELECT pg_catalog.setval('inventory_inventory_id_seq', COALESCE((SELECT MAX(inventory_id) FROM inventory), 1), true);
SELECT pg_catalog.setval('reviews_feedbacks_review_id_seq', COALESCE((SELECT MAX(review_id) FROM reviews_feedbacks), 1), true);
SELECT pg_catalog.setval('carts_cart_id_seq', COALESCE((SELECT MAX(cart_id) FROM carts), 1), true);
SELECT pg_catalog.setval('orders_order_id_seq', COALESCE((SELECT MAX(order_id) FROM orders), 1), true);


\echo 'Verification Counts:'
SELECT COUNT(*) AS user_count FROM accounts;
SELECT COUNT(*) AS category_count FROM products_categories;
SELECT COUNT(*) AS product_count FROM products;
SELECT COUNT(*) AS inventory_count FROM inventory;
SELECT COUNT(*) AS review_count FROM reviews_feedbacks;
SELECT COUNT(*) AS cart_count FROM carts;
SELECT COUNT(*) AS cart_product_count FROM cart_products;
SELECT COUNT(*) AS order_count FROM orders;
SELECT COUNT(*) AS order_item_count FROM orders_products;