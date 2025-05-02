# index.py
from flask import render_template, request, flash, app, redirect, url_for
from flask_login import login_required, current_user
from .models.orders import OrderItem
from datetime import datetime
from .models.orders import Order
from .models.product import Product
from .models.review import Review
from flask import Blueprint

bp = Blueprint('index', __name__)


@bp.route('/')
def index():
    search_query = request.args.get('search', '')
    filter_type = request.args.get('filter', '')
    top_k = request.args.get('top_k', type=int, default=5)
    sort_by = request.args.get('sort_by', 'name')
    sort_dir = request.args.get('sort_dir', 'asc')

    page = request.args.get('page', 1, type=int)
    per_page = 12  # Number of products per page

    if top_k < 1:
        top_k = 5

    if filter_type == 'expensive':
        products = Product.get_top_k_expensive(top_k)
    else:
        if sort_by == 'price':
            all_products = Product.get_all(True)
            for product in all_products:
                inventory_items = product.get_inventory_items()
                if inventory_items:
                    product.price = min(item.unit_price for item in inventory_items)
                else:
                    product.price = 0.00

            products = sorted(all_products,
                              key=lambda p: p.price if p.price is not None else 0.0,
                              reverse=(sort_dir == 'desc'))

            total_products = len(products)
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            products = products[start_idx:end_idx]
        else:
            products = Product.search(
                query=search_query,
                sort_by=sort_by,
                sort_dir=sort_dir,
                limit=per_page,
                offset=(page - 1) * per_page
            )
            total_products = Product.count_search_results(query=search_query)

    for product in products:
        if not hasattr(product, 'price') or product.price is None:
            inventory_items = product.get_inventory_items()
            if inventory_items:
                product.price = min(item.unit_price for item in inventory_items)
                product.available_seller_id = inventory_items[0].seller_id##
            else:
                product.price = 0.00
                product.available_seller_id = None

    if current_user.is_authenticated:
        purchases = Order.get_for_buyer(current_user.id)
    else:
        purchases = None

    total_pages = (total_products + per_page - 1) // per_page
    has_prev = page > 1
    has_next = page < total_pages

    return render_template('index.html',
                           avail_products=products,
                           purchase_history=purchases,
                           search_query=search_query,
                           filter_type=filter_type,
                           top_k=top_k,
                           sort_by=sort_by,
                           sort_dir=sort_dir,
                           page=page,
                           total_pages=total_pages,
                           has_prev=has_prev,
                           has_next=has_next,
                           per_page=per_page,
                           total_products=total_products)


@bp.route('/purchase-history')
@login_required
def purchase_history():
    # Get filter parameters from request
    search_query = request.args.get('search', '')
    seller_id = request.args.get('seller_id', type=int)
    product_id = request.args.get('product_id', type=int)
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    status = request.args.get('status', '')
    sort_by = request.args.get('sort_by', 'date')
    sort_order = request.args.get('sort_order', 'desc')

    # Convert date strings to datetime objects if they exist
    from_date = None
    to_date = None
    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d')
        except ValueError:
            flash('Invalid from date format. Please use YYYY-MM-DD', 'error')

    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d')
            # Set time to end of day
            to_date = to_date.replace(hour=23, minute=59, second=59)
        except ValueError:
            flash('Invalid to date format. Please use YYYY-MM-DD', 'error')

    # Get orders with filters
    orders = Order.get_filtered_orders(
        buyer_id=current_user.id,
        search_query=search_query,
        seller_id=seller_id,
        product_id=product_id,
        from_date=from_date,
        to_date=to_date,
        status=status,
        sort_by=sort_by,
        sort_order=sort_order
    )

    # Get list of sellers and products for filter dropdowns
    sellers = []
    products = []

    # Only fetch these if user has orders
    if orders:
        sellers = Order.get_sellers_for_buyer(current_user.id)
        products = Order.get_products_for_buyer(current_user.id)

    return render_template(
        'purchase_history.html',
        orders=orders,
        sellers=sellers,
        products=products,
        filters={
            'search': search_query,
            'seller_id': seller_id,
            'product_id': product_id,
            'date_from': from_date,
            'date_to': to_date,
            'status': status,
            'sort_by': sort_by,
            'sort_order': sort_order
        }
    )

# 2. Now add the necessary methods to the Order class in orders.py

# Add these methods to the Order class in orders.py
@staticmethod
def get_filtered_orders(buyer_id, search_query=None, seller_id=None, product_id=None,
                        from_date=None, to_date=None, status=None,
                        sort_by='date', sort_order='desc'):
    """Get filtered orders for a buyer"""

    # Start building the query
    query = '''
        SELECT DISTINCT o.order_id, o.buyer_id, o.total_amount, o.order_date, 
               o.num_products, o.order_status, CONCAT(a.first_name, ' ', a.last_name) AS buyer_name, 
               a.address
        FROM Orders o
        JOIN Orders_Products op ON o.order_id = op.order_id
        JOIN Products p ON op.product_id = p.product_id
        JOIN Accounts a ON o.buyer_id = a.user_id
        JOIN Accounts s ON op.seller_id = s.user_id
        WHERE o.buyer_id = :buyer_id
    '''

    # Initialize parameters dictionary
    params = {'buyer_id': buyer_id}

    # Add filter conditions
    if search_query:
        query += ''' AND (
            p.product_name ILIKE :search_query OR
            CONCAT(s.first_name, ' ', s.last_name) ILIKE :search_query
        )'''
        params['search_query'] = f'%{search_query}%'

    if seller_id:
        query += ' AND op.seller_id = :seller_id'
        params['seller_id'] = seller_id

    if product_id:
        query += ' AND op.product_id = :product_id'
        params['product_id'] = product_id

    if from_date:
        query += ' AND o.order_date >= :from_date'
        params['from_date'] = from_date

    if to_date:
        query += ' AND o.order_date <= :to_date'
        params['to_date'] = to_date

    if status:
        query += ' AND o.order_status = :status'
        params['status'] = status

    # Add sorting
    if sort_by == 'price':
        query += ' ORDER BY o.total_amount'
    elif sort_by == 'status':
        query += ' ORDER BY o.order_status'
    else:  # default to date
        query += ' ORDER BY o.order_date'

    # Add sort direction
    query += ' DESC' if sort_order == 'desc' else ' ASC'

    # Execute query
    rows = app.db.execute(query, **params)

    # Process results
    orders = []
    for row in rows:
        order = Order(*row)
        # Get items for each order
        order.items = OrderItem.get_for_order(order.order_id)
        orders.append(order)

    return orders


@staticmethod
def get_sellers_for_buyer(buyer_id):
    """Get list of sellers that the buyer has ordered from"""
    rows = app.db.execute('''
        SELECT DISTINCT s.user_id, CONCAT(s.first_name, ' ', s.last_name) AS seller_name
        FROM Orders o
        JOIN Orders_Products op ON o.order_id = op.order_id
        JOIN Accounts s ON op.seller_id = s.user_id
        WHERE o.buyer_id = :buyer_id
        ORDER BY seller_name
    ''', buyer_id=buyer_id)

    return [{'id': row[0], 'name': row[1]} for row in rows]


@staticmethod
def get_products_for_buyer(buyer_id):
    """Get list of products that the buyer has ordered"""
    rows = app.db.execute('''
        SELECT DISTINCT p.product_id, p.product_name
        FROM Orders o
        JOIN Orders_Products op ON o.order_id = op.order_id
        JOIN Products p ON op.product_id = p.product_id
        WHERE o.buyer_id = :buyer_id
        ORDER BY p.product_name
    ''', buyer_id=buyer_id)

    return [{'id': row[0], 'name': row[1]} for row in rows]


# @bp.route('/order/<int:order_id>')
# @login_required
# def view_order_details(order_id):
#     # Get the order
#     order = Order.get(order_id)
#
#     # Check if order exists and belongs to the current user
#     if not order or order.buyer_id != current_user.id:
#         flash('Order not found or you do not have permission to view it', 'error')
#         return redirect(url_for('index.purchase_history'))
#
#     # Group items by seller
#     sellers = {}
#     for item in order.items:
#         if item.seller_id not in sellers:
#             sellers[item.seller_id] = {
#                 'id': item.seller_id,
#                 'name': item.seller_name,
#                 'products': [],  # Changed from 'items' to 'products'
#                 'subtotal': 0,
#                 'status': 'Fulfilled'  # Will be set to 'Unfulfilled' if any item is unfulfilled
#             }
#
#         # Add item to seller group
#         item.image = f"/static/uploads/{item.image}"
#         sellers[item.seller_id]['products'].append(item)  # Changed from 'items' to 'products'
#
#         # Add to seller subtotal
#         sellers[item.seller_id]['subtotal'] += item.get_subtotal()
#
#         # Update seller group status
#         if item.status == 'Unfulfilled':
#             sellers[item.seller_id]['status'] = 'Unfulfilled'
#
#     # Convert to list for template
#     seller_groups = list(sellers.values())
#
#     return render_template(
#         'order_details.html',
#         order=order,
#         seller_groups=seller_groups
#     )

@bp.route('/order/<int:order_id>')
@login_required
def view_order_details(order_id):
    # Get the order
    order = Order.get(order_id)

    # Check if order exists and belongs to the current user
    if not order or order.buyer_id != current_user.id:
        flash('Order not found or you do not have permission to view it', 'error')
        return redirect(url_for('index.purchase_history'))

    # Get seller IDs from items
    seller_ids = [item.seller_id for item in order.items]

    # Get seller reviews to check if user has already reviewed any seller
    seller_reviews = []
    if seller_ids:
        seller_reviews = Review.get_user_reviews_for_sellers(current_user.id, seller_ids)

    # Get product reviews to check if user has already reviewed any product
    product_ids = [item.product_id for item in order.items]
    product_reviews = []
    if product_ids:
        product_reviews = Review.get_user_reviews_for_products(current_user.id, product_ids)

    # Get seller ratings
    seller_ratings = {}
    for seller_id in seller_ids:
        avg_rating, _ = Review.get_avg_rating_seller(seller_id)
        if avg_rating:
            seller_ratings[seller_id] = avg_rating

    # Group items by seller
    sellers = {}
    for item in order.items:
        if item.seller_id not in sellers:
            sellers[item.seller_id] = {
                'id': item.seller_id,
                'name': item.seller_name,
                'products': [],
                'subtotal': 0,
                'status': 'Fulfilled'
            }

        # Add item to seller group
        sellers[item.seller_id]['products'].append(item)

        # Add to seller subtotal
        sellers[item.seller_id]['subtotal'] += item.get_subtotal()

        # Update seller group status
        if item.status == 'Unfulfilled':
            sellers[item.seller_id]['status'] = 'Unfulfilled'

    # Convert to list for template
    seller_groups = list(sellers.values())

    return render_template(
        'order_details.html',
        order=order,
        seller_groups=seller_groups,
        seller_reviews=seller_reviews,
        product_reviews=product_reviews,
        seller_ratings=seller_ratings
    )