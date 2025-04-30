-- Drop tables if they exist (in reverse order of dependencies)
DROP TABLE IF EXISTS Orders_Products CASCADE;
DROP TABLE IF EXISTS Orders CASCADE;
DROP TABLE IF EXISTS Inventory CASCADE;
DROP TABLE IF EXISTS Products CASCADE;
DROP TABLE IF EXISTS Carts CASCADE;
DROP TABLE IF EXISTS Accounts CASCADE;
DROP TABLE IF EXISTS Reviews_Feedbacks CASCADE;
DROP TABLE IF EXISTS Cart_Products CASCADE;
DROP TABLE IF EXISTS Products_Categories CASCADE;

-- Create Accounts table
CREATE TABLE Accounts (
    user_id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    address TEXT,
    password VARCHAR(255) NOT NULL,
    current_balance DECIMAL(10,2) DEFAULT 0.00,
    is_seller BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Products_Categories table
CREATE TABLE Products_Categories (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Products table
CREATE TABLE Products (
    product_id SERIAL PRIMARY KEY,
    category_id INT NOT NULL,
    product_name VARCHAR(100) NOT NULL,
    description TEXT,
    image VARCHAR(255),
    owner_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES Products_Categories(category_id),
    FOREIGN KEY (owner_id) REFERENCES Accounts(user_id)
);

-- Create Inventory table
CREATE TABLE Inventory (
    inventory_id SERIAL PRIMARY KEY,
    seller_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 0,
    unit_price DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    owner_id INT,
    UNIQUE(seller_id, product_id),
    FOREIGN KEY (seller_id) REFERENCES Accounts(user_id),
    FOREIGN KEY (product_id) REFERENCES Products(product_id),
    FOREIGN KEY (owner_id) REFERENCES Accounts(user_id)
);

-- Create Carts table
CREATE TABLE Carts (
    cart_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Accounts(user_id)
);

-- Create Cart_Products junction table
CREATE TABLE Cart_Products (
    cart_id INT NOT NULL,
    product_id INT NOT NULL,
    seller_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    price_at_addition DECIMAL(10,2) NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'in_cart',
    PRIMARY KEY (cart_id, product_id, seller_id),
    FOREIGN KEY (cart_id) REFERENCES Carts(cart_id),
    FOREIGN KEY (product_id) REFERENCES Products(product_id),
    FOREIGN KEY (seller_id) REFERENCES Accounts(user_id),
    CHECK (status IN ('in_cart', 'saved_for_later'))
);
-- Create Reviews_Feedbacks table
CREATE TABLE Reviews_Feedbacks (
    review_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    product_id INT,
    seller_id INT,
    comment TEXT NOT NULL,
    review_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    rating INT NOT NULL,
    upvotes INT DEFAULT 0 NOT NULL,
    downvotes INT DEFAULT 0 NOT NULL,
    FOREIGN KEY (user_id) REFERENCES Accounts(user_id),
    FOREIGN KEY (product_id) REFERENCES Products(product_id),
    FOREIGN KEY (seller_id) REFERENCES Accounts(user_id),
    UNIQUE (user_id, product_id),  -- User can only review a product once
    UNIQUE (user_id, seller_id),   -- User can only review a seller once
    CHECK (
        (product_id IS NOT NULL AND seller_id IS NULL) OR
        (product_id IS NULL AND seller_id IS NOT NULL)
    ),
    CHECK (rating >= 1 AND rating <= 5)
);
CREATE TABLE ReviewVotes (
    vote_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    review_id INT NOT NULL,
    vote_type INT NOT NULL, -- 1 for upvote, -1 for downvote
    voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Accounts(user_id),
    FOREIGN KEY (review_id) REFERENCES Reviews_Feedbacks(review_id) ON DELETE CASCADE, -- Delete vote if review is deleted
    UNIQUE (user_id, review_id), -- Ensure one vote per user per review
    CHECK (vote_type IN (1, -1)) -- Ensure vote_type is either 1 or -1
);
CREATE INDEX idx_reviewvotes_review ON ReviewVotes(review_id);
CREATE INDEX idx_reviewvotes_user_review ON ReviewVotes(user_id, review_id);
CREATE INDEX idx_reviews_helpfulness ON Reviews_Feedbacks((upvotes - downvotes) DESC, review_date DESC);





-- Create Orders table
CREATE TABLE Orders (
    order_id SERIAL PRIMARY KEY,
    buyer_id INT NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    num_products INT NOT NULL,
    order_status VARCHAR(20) NOT NULL DEFAULT 'Unfulfilled',
    CHECK (order_status IN ('Unfulfilled', 'Fulfilled')),
    FOREIGN KEY (buyer_id) REFERENCES Accounts(user_id)
);

-- Create Orders_Products junction table
CREATE TABLE Orders_Products (
    order_item_id SERIAL PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    seller_id INT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Unfulfilled',
    fulfillment_date TIMESTAMP,
    CHECK (status IN ('Unfulfilled', 'Fulfilled')),
    FOREIGN KEY (order_id) REFERENCES Orders(order_id),
    FOREIGN KEY (product_id) REFERENCES Products(product_id),
    FOREIGN KEY (seller_id) REFERENCES Accounts(user_id),
    UNIQUE (order_id, product_id, seller_id)
);

-- Update the owner_id in Inventory table based on product ownership
UPDATE Inventory i
SET owner_id = (
    SELECT owner_id
    FROM Products p
    WHERE p.product_id = i.product_id
);

-- Create indexes for foreign keys to improve query performance
CREATE INDEX idx_products_category ON Products(category_id);
CREATE INDEX idx_products_owner ON Products(owner_id);
CREATE INDEX idx_inventory_seller ON Inventory(seller_id);
CREATE INDEX idx_inventory_product ON Inventory(product_id);
CREATE INDEX idx_cart_user ON Carts(user_id);
CREATE INDEX idx_cart_products_cart ON Cart_Products(cart_id);
CREATE INDEX idx_cart_products_product ON Cart_Products(product_id);
CREATE INDEX idx_cart_products_seller ON Cart_Products(seller_id);
CREATE INDEX idx_reviews_user ON Reviews_Feedbacks(user_id);
CREATE INDEX idx_reviews_product ON Reviews_Feedbacks(product_id);
CREATE INDEX idx_reviews_seller ON Reviews_Feedbacks(seller_id);
CREATE INDEX idx_orders_buyer ON Orders(buyer_id);
CREATE INDEX idx_orders_products_order ON Orders_Products(order_id);
CREATE INDEX idx_orders_products_product ON Orders_Products(product_id);
CREATE INDEX idx_orders_products_seller ON Orders_Products(seller_id);
CREATE INDEX idx_cart_products_cart ON Cart_Products(cart_id);
CREATE INDEX idx_cart_products_product ON Cart_Products(product_id);
CREATE INDEX idx_cart_products_seller ON Cart_Products(seller_id);
-- <<< Optional: Add index on status for faster filtering
CREATE INDEX idx_cart_products_status ON Cart_Products(status);
-- Add comments to tables
COMMENT ON TABLE Accounts IS 'Stores user account information for both buyers and sellers';
COMMENT ON TABLE Products_Categories IS 'Categories for products (e.g., Electronics, Clothing)';
COMMENT ON TABLE Products IS 'Product information catalog';
COMMENT ON TABLE Inventory IS 'Product inventory with quantity and pricing information per seller';
COMMENT ON TABLE Carts IS 'Shopping carts for users';
COMMENT ON TABLE Cart_Products IS 'Products in users shopping carts';
COMMENT ON TABLE Reviews_Feedbacks IS 'Reviews for either products or sellers';
COMMENT ON TABLE Orders IS 'Order information';
COMMENT ON TABLE Orders_Products IS 'Products within an order with specific seller and status';

-- Create views to simplify complex queries
CREATE OR REPLACE VIEW product_details AS
SELECT
    p.product_id,
    p.product_name,
    p.description,
    p.image,
    p.category_id,
    pc.category_name,
    p.owner_id,
    CONCAT(COALESCE(a.first_name, ''), ' ', COALESCE(a.last_name, '')) AS owner_name,
    p.created_at,
    p.updated_at,
    COALESCE(AVG(r.rating), 0) AS average_rating,
    COUNT(r.review_id) AS review_count
FROM Products p
JOIN Products_Categories pc ON p.category_id = pc.category_id
JOIN Accounts a ON p.owner_id = a.user_id
LEFT JOIN Reviews_Feedbacks r ON p.product_id = r.product_id
GROUP BY p.product_id, pc.category_name, a.first_name, a.last_name;

CREATE OR REPLACE VIEW inventory_details AS
SELECT
    i.inventory_id,
    i.seller_id,
    CONCAT(a.first_name, ' ', a.last_name) AS seller_name,
    i.product_id,
    p.product_name,
    p.category_id,
    pc.category_name,
    p.image,
    i.quantity,
    i.unit_price,
    i.created_at,
    i.updated_at,
    COALESCE(AVG(r.rating), 0) AS seller_rating
FROM Inventory i
JOIN Accounts a ON i.seller_id = a.user_id
JOIN Products p ON i.product_id = p.product_id
JOIN Products_Categories pc ON p.category_id = pc.category_id
LEFT JOIN Reviews_Feedbacks r ON i.seller_id = r.seller_id
GROUP BY i.inventory_id, a.first_name, a.last_name, p.product_name, p.category_id, pc.category_name, p.image;


CREATE INDEX idx_products_name_search ON Products USING gin(to_tsvector('simple', product_name));

CREATE INDEX idx_products_description_search ON Products USING gin(to_tsvector('simple', description));

CREATE INDEX idx_products_category_name ON Products(category_id, product_name);

CREATE INDEX idx_inventory_price_quantity ON Inventory(unit_price, quantity);


CREATE INDEX idx_accounts_email_password ON Accounts(email, password);

CREATE INDEX idx_accounts_seller ON Accounts(is_seller) WHERE is_seller = TRUE;


CREATE INDEX idx_orders_buyer_date ON Orders(buyer_id, order_date DESC);

CREATE INDEX idx_orders_products_seller_status ON Orders_Products(seller_id, status) WHERE status = 'Unfulfilled';

CREATE INDEX idx_orders_date_amount ON Orders(order_date DESC, total_amount);


CREATE INDEX idx_inventory_low_stock ON Inventory(seller_id, quantity) WHERE quantity < 10;

CREATE INDEX idx_inventory_product_price ON Inventory(product_id, unit_price);


CREATE INDEX idx_reviews_product_rating ON Reviews_Feedbacks(product_id, rating DESC);

CREATE INDEX idx_reviews_seller_rating ON Reviews_Feedbacks(seller_id, rating DESC);

CREATE INDEX idx_reviews_date ON Reviews_Feedbacks(review_date DESC);


CREATE INDEX idx_carts_user_updated ON Carts(user_id, updated_at DESC);

CREATE INDEX idx_inventory_category_price ON Inventory(product_id, unit_price)
WITH (product_id IN (SELECT product_id FROM Products WHERE category_id = :category_id));

CREATE INDEX idx_orders_date_range ON Orders(order_date)
WHERE order_date > CURRENT_DATE - INTERVAL '30 days';