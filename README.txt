Gingerbread Standard Project
Project Overview:
The Gingerbread Standard Project is a web-based e-commerce platform designed to facilitate seamless transactions between buyers and sellers. The platform provides functionalities for user account management, product browsing, cart management, order fulfillment, and social interactions such as reviews and messaging.

This project is being developed collaboratively by a team of five, each specializing in a different aspect of the system.

Final milestone demo video: 
https://www.youtube.com/watch?v=ENlNnMFfgxc

GitLab Repository:
https://gitlab.oit.duke.edu/Cindy_Gao/gingerbread-standard-project


Team Roles & Responsibilities:
Users Guru (Hongyi Duan): responsible for Account / Purchases
1. Designed the Account table and implemented the following features:
    i. User Registration & Authentication: Users can register, log in, log out, and reset their passwords.
    ii. User Profile Management: Allows users to edit their profile details (email, name, address, password).
    iii. Balance Management: Implemented top-up, withdrawal, and transaction history tracking.
2. Created the README.txt and documented the project details.
3. Implement search/filter functionality for purchase history by item, seller, date, etc.
4. Set up and managed the project GitLab repository.
5. Designed all the web pages.

Products Guru (Jiaxin Gao): responsible for Products
1. Designed the Products table, identifying ProductID as the primary key.
2. Created the preliminary website page-by-page design.
3. Developed functionalities for:
    i. Product search, filtering, and sorting.
    ii. Viewing detailed product information.
    iii. Managing product availability by different sellers.
4. Implement low stock warning in the seller dashboard if a product's available quantity is below 5, marked as "low stock" in red font.
5. Designed the Entity-Relationship Diagram (ERD) that integrates all database tables.

Carts Guru (Yizhe Chen): responsible for Cart / Order
1. Designed the Orders table, with OrderID as the primary key.
2. Created the preliminary website page-by-page design.
3. Developed functionalities for:
    i. Cart Management: Users can add/remove items and adjust quantities.
    ii. Order Processing: Checkout system and order confirmation.
    iii. Order Tracking: Users can reorder items, track status, and request refunds.
4. Divide the cart into "in cart" and "saved for later" sections, allowing users to check out certain items and save others for later.

Sellers Guru (Zhikang Song): responsible for Inventory / Order Fulfillment
1. Designed the Inventory table, allowing seller users to:
    i. Add new products.
    ii. Update stock quantities.
    iii. Delete products.
2. Started backend database implementation for inventory and order fulfillment.
3. Developed functionalities for:
    i. Seller Dashboard: Manage products and track orders.
    ii. Order Fulfillment: View buyer details and mark orders as fulfilled.
4. Add visualization/analytics to the inventory and/or order fulfillment pages to show product popularity and trends.

Social Guru (Hongxi Chen): responsible for Feedback / Messaging
1. Implemented the User Reviews system, enabling users to:
    i. Submit ratings and written reviews.
    ii. Edit and delete their reviews.
    iii. Sort and filter reviews based on criteria such as date and rating.
2. Developed public profile views, including:
    i. Viewing seller reviews.
    ii. Contacting sellers for inquiries.
3. Worked on messaging and feedback systems to enhance user interaction.
4. Implement upvote functionality for reviews, allowing users to mark reviews as more or less helpful, with top 3 helpful reviews shown first.


## Project Structure

```text
GINGERBREAD-STANDARD-PROJECT/
├── app/
│   ├── db/
│   │   ├── data/
│   │   │   ├── enhanced/        # Original preprocessed CSVs
│   │   │   └── generated/       # System‑generated CSVs
│   ├── models/                  # ORM model definitions
│   │   ├── cart.py
│   │   ├── inventory.py
│   │   ├── orders.py
│   │   ├── product.py
│   │   ├── purchase.py
│   │   ├── review.py
│   │   └── user.py
│   ├── static/                  # CSS, JS, images
│   ├── templates/               # HTML templates
│   │   ├── seller/              # Seller‑specific pages
│   │   ├── add_review.html
│   │   ├── cart.html
│   │   ├── edit_review.html
│   │   ├── index.html
│   │   ├── layout.html
│   │   ├── login.html
│   │   ├── product_detail.html
│   │   ├── product_reviews.html
│   │   ├── profile.html
│   │   ├── purchase_history.html
│   │   ├── register.html
│   │   ├── reviews.html
│   │   ├── seller_reviews.html
│   │   └── topup.html
│   ├── carts.py
│   ├── config.py
│   ├── data_generator.py
│   ├── db.py
│   ├── index.py
│   ├── products.py
│   ├── reviews.py
│   ├── seller.py
│   └── users.py
├── db/
│   ├── data/
│   │   ├── insert_users.sql
│   │   ├── order_products.csv
│   │   ├── Products.csv
│   │   ├── Purchases.csv
│   │   ├── Reviews.csv
│   │   └── Users.csv
│   ├── generated/
│   │   ├── gen.py
│   │   ├── Products.csv
│   │   ├── Purchases.csv
│   │   └── Users.csv
│   ├── create.sql
│   └── load.sql
├── setup.sh                      # Setup database & data
├── install.sh                    # Install dependencies
├── amazon.py                     # Flask application entry point
├── environment.yml               # Conda environment spec
├── .flaskenv                     # Flask CLI configuration
├── .gitignore
├── LICENSE
├── README.md
└── FAQ.md