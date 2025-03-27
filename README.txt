Gingerbread Standard Project
Project Overview:
The Gingerbread Standard Project is a web-based e-commerce platform designed to facilitate seamless transactions between buyers and sellers. The platform provides functionalities for user account management, product browsing, cart management, order fulfillment, and social interactions such as reviews and messaging.

This project is being developed collaboratively by a team of five, each specializing in a different aspect of the system.


Team Roles & Responsibilities:
Users Guru (Jiaxin Gao): responsible for Account / Purchases
1. Designed the Account table and implemented the following features:
    i. User Registration & Authentication: Users can register, log in, log out, and reset their passwords.
    ii. User Profile Management: Allows users to edit their profile details (email, name, address, password).
    iii. Balance Management: Implemented top-up, withdrawal, and transaction history tracking.
2. Created the README.txt and documented the project details.
3. Designed the Entity-Relationship Diagram (ERD) that integrates all database tables.
4. Set up and managed the project GitLab repository.

Products Guru (Hongyi Duan): responsible for Products
1. Designed the Products table, identifying ProductID as the primary key.
2. Created the preliminary website page-by-page design with Yizhe Chen.
3. Developed functionalities for:
    i. Product search, filtering, and sorting.
    ii. Viewing detailed product information.
    iii. Managing product availability by different sellers.

Carts Guru (Yizhe Chen): responsible for Cart / Order
1. Designed the Orders table, with OrderID as the primary key.
2. Created the preliminary website page-by-page design with Hongyi Duan.
3. Developed functionalities for:
    i. Cart Management: Users can add/remove items and adjust quantities.
    ii. Order Processing: Checkout system and order confirmation.
    iii. Order Tracking: Users can reorder items, track status, and request refunds.


Sellers Guru (Zhikang Song): responsible for Inventory / Order Fulfillment
1. Designed the Inventory table, allowing seller users to:
    i. Add new products.
    ii. Update stock quantities.
    iii. Delete products.
2. Started backend database implementation for inventory and order fulfillment with Hongyi Chen.
3. Developed functionalities for:
    i. Seller Dashboard: Manage products and track orders.
    ii. Order Fulfillment: View buyer details and mark orders as fulfilled.

Social Guru (Hongxi Chen): responsible for Feedback / Messaging
1. Implemented the User Reviews system, enabling users to:
    i. Submit ratings and written reviews.
    ii. Edit and delete their reviews.
    iii. Sort and filter reviews based on criteria such as date and rating.
2. Developed public profile views, including:
    i. Viewing seller reviews.
    ii. Contacting sellers for inquiries.
3. Worked on messaging and feedback systems to enhance user interaction.

GitLab Repository:
https://gitlab.oit.duke.edu/Cindy_Gao/gingerbread-standard-project

1. User Authentication & Profile
Routes in users.py:

/login (GET/POST): User login form and processing
/register (GET/POST): User registration form and processing
/logout (GET): Log out the current user
/profile (GET): Display user profile
/topup (GET/POST): Add balance to user account

2. Product Management
Routes in product.py:

/products/<product_id> (GET): Display product details
/products/api/<product_id> (GET): JSON API endpoint for product data

3. Cart Management
Routes in cart.py:

/cart/ (GET): View cart contents
/cart/add (POST): Add a product to cart
/cart/remove (POST): Remove a product from cart
/cart/update (POST): Update product quantity in cart

4. Seller Management
Routes in seller.py:

/seller/dashboard (GET): Seller overview dashboard
/seller/inventory (GET): View seller's inventory
/seller/inventory/add (GET/POST): Add new product to inventory
/seller/inventory/edit/<inventory_id> (GET/POST): Edit inventory item
/seller/inventory/delete/<inventory_id> (POST): Remove product from inventory
/seller/orders (GET): View all orders to be fulfilled
/seller/orders/<order_id> (GET): View details of a specific order
/seller/orders/fulfill/<order_item_id> (POST): Mark an order item as fulfilled

5. Review System
Routes in reviews.py:

/user-reviews (GET): View all reviews by current user
/api/reviews/recent/<user_id> (GET): Get recent reviews for a user
/reviews/<user_id> (GET): View public reviews for a user
/reviews/add (GET/POST): Add a new review
/reviews/edit/<review_id> (GET/POST): Edit an existing review
/api/reviews/delete/<review_id> (DELETE): Delete a review
/reviews/product/<product_id> (GET): View reviews for a product
/reviews/seller/<seller_id> (GET): View reviews for a seller

6. Main / Index
Routes in index.py:

/ (GET): Main landing page showing products and purchase history