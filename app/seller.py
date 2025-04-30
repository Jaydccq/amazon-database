import logging

from flask import Blueprint, render_template, request, redirect, url_for
from flask import flash, session, current_app, jsonify, app
from functools import wraps
from werkzeug.utils import secure_filename
import os
from datetime import datetime

from .models.inventory import Inventory
from .models.orders import Order, OrderItem
from .models.product import Product, Category

bp = Blueprint('seller', __name__, url_prefix='/seller')


# Helper function to check if user is logged in as a seller
def seller_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            print(session)
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('users.login'))

        if not session.get('is_seller'):
            flash('You must be registered as a seller to access this page.', 'error')
            print(session)
            return redirect(url_for('index.index'))

        return f(*args, **kwargs)

    return decorated_function


@bp.route('/dashboard')
@seller_required
def dashboard():
    """Seller dashboard overview"""
    user_id = session['user_id']

    # Get recent orders (first page)
    recent_orders = Order.get_for_seller(
        user_id,
        limit=5,
        status='Unfulfilled'
    )

    # Get inventory statistics
    inventory_items = Inventory.get_for_seller(
        user_id,
        limit=100  # Get enough items to calculate statistics
    )

    # Calculate total inventory value
    total_value = sum(item.quantity * float(item.unit_price) for item in inventory_items)

    # Count items with low stock
    low_stock_count = sum(1 for item in inventory_items if item.quantity < 5)

    # Get total number of orders
    fulfilled_orders = Order.count_for_seller(user_id, status='Fulfilled')
    unfulfilled_orders = Order.count_for_seller(user_id, status='Unfulfilled')

    return render_template(
        'seller/dashboard.html',
        recent_orders=recent_orders,
        inventory_items=inventory_items[:5],  # Only display the first 5
        total_value=total_value,
        low_stock_count=low_stock_count,
        inventory_count=len(inventory_items),
        fulfilled_orders=fulfilled_orders,
        unfulfilled_orders=unfulfilled_orders
    )


@bp.route('/inventory')
@seller_required
def inventory():
    """Seller inventory management"""
    user_id = session['user_id']

    page = request.args.get('page', 1, type=int)
    search = request.args.get('search')
    category_id = request.args.get('category_id')

    # Items per page
    per_page = 10

    # Get inventory items with pagination
    inventory_items = Inventory.get_for_seller(
        user_id,
        limit=per_page,
        offset=(page - 1) * per_page,
        search_query=search,
        category_id=category_id
    )

    # change image path for each item
    for item in inventory_items:
        if item.image:
            item.image = f"/static/uploads/{item.image}"
        else:
            item.image = "/static/uploads/image-default.png"

    # Get total count for pagination
    total_items = Inventory.count_for_seller(
        user_id,
        search_query=search,
        category_id=category_id
    )

    # Get categories for filter dropdown
    categories = Category.get_all()

    return render_template(
        'seller/inventory.html',
        inventory_items=inventory_items,
        categories=categories,
        current_category=category_id,
        search_query=search,
        pagination={
            'page': page,
            'per_page': per_page,
            'total': total_items,
            'pages': (total_items + per_page - 1) // per_page
        }
    )


@bp.route('/inventory/add', methods=['GET', 'POST'])
@seller_required
def add_inventory():
    """Add product to inventory"""
    user_id = session['user_id']

    if request.method == 'POST':
        # Existing POST logic remains unchanged
        product_id = request.form.get('product_id', type=int)
        quantity = request.form.get('quantity', type=int)
        unit_price = request.form.get('unit_price', type=float)

        # Validate inputs
        if not product_id or not quantity or not unit_price:
            flash('All fields are required', 'error')
            return redirect(url_for('seller.add_inventory'))

        if quantity < 0:
            flash('Quantity cannot be negative', 'error')
            return redirect(url_for('seller.add_inventory'))

        if unit_price <= 0:
            flash('Price must be greater than zero', 'error')
            return redirect(url_for('seller.add_inventory'))

        # Check if product exists
        product = Product.get(product_id)
        if not product:
            flash('Product not found', 'error')
            return redirect(url_for('seller.add_inventory'))

        # Check if already in inventory
        existing = Inventory.get_by_seller_and_product(user_id, product_id)
        if existing:
            flash('This product is already in your inventory', 'error')
            return redirect(url_for('seller.add_inventory'))

        # Add to inventory
        inventory_id = Inventory.create(user_id, product_id, quantity, unit_price)

        if inventory_id:
            flash('Product added to inventory', 'success')
            return redirect(url_for('seller.inventory'))
        else:
            flash('Failed to add product to inventory', 'error')
            return redirect(url_for('seller.add_inventory'))

    # GET request handling with pagination
    # Get search parameters
    search_query = request.args.get('search', '')
    current_category = request.args.get('category_id', '')
    page = request.args.get('page', 1, type=int)
    per_page = 9  # 9 items (3x3 grid) per page

    # Get all products first
    all_products = Product.get_all()
    filtered_products = []

    # Apply filters if needed
    for p in all_products:
        # Skip if category filter is active and doesn't match
        if current_category and str(p.category_id) != current_category:
            continue

        # Skip if search is active and doesn't match
        if search_query and search_query.lower() not in p.product_name.lower():
            continue

        filtered_products.append(p)

    # Get existing inventory product IDs
    existing_inventory = Inventory.get_for_seller(user_id)
    existing_product_ids = {item.product_id for item in existing_inventory}

    # Filter out products already in inventory
    available_products = [p for p in filtered_products if p.id not in existing_product_ids]

    # Calculate total items and pages for pagination
    total_items = len(available_products)
    total_pages = (total_items + per_page - 1) // per_page

    # Apply pagination - slice the available products
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paged_products = available_products[start_idx:end_idx]

    # Get categories for grouping products
    categories = {cat.id: cat.name for cat in Category.get_all()}

    # Make sure Product objects have the right attributes for the template
    for p in paged_products:
        # Add id and name attributes if they don't exist
        if not hasattr(p, 'id'):
            p.id = p.product_id
        if not hasattr(p, 'name'):
            p.name = p.product_name

    return render_template(
        'seller/add_inventory.html',
        available_products=paged_products,
        categories=categories,
        search_query=search_query,
        current_category=current_category,
        pagination={
            'page': page,
            'per_page': per_page,
            'total': total_items,
            'pages': total_pages
        }
    )


@bp.route('/product/create', methods=['GET', 'POST'])
@seller_required
def create_product():
    """Create a new product"""
    user_id = session['user_id']

    if request.method == 'POST':
        # Get form data
        product_name = request.form.get('product_name')
        category_id = request.form.get('category_id', type=int)
        description = request.form.get('description')
        quantity = request.form.get('quantity', type=int)
        unit_price = request.form.get('unit_price', type=float)

        # log the inputs for debugging
        print(f"Product Name: {product_name}, Category ID: {category_id}, Description: {description}, Quantity: {quantity}, Unit Price: {unit_price}")
        # Validate inputs
        if (product_name is None or product_name == '' or
                category_id is None or
                description is None or description == '' or
                quantity is None or
                unit_price is None):
            flash('All required fields must be filled out', 'error')
            return redirect(url_for('seller.create_product'))

        if quantity < 0:
            flash('Quantity cannot be negative', 'error')
            return redirect(url_for('seller.create_product'))

        if unit_price <= 0:
            flash('Price must be greater than zero', 'error')
            return redirect(url_for('seller.create_product'))

        # Handle image upload
        image_url = None
        if 'product_image' in request.files:
            file = request.files['product_image']
            if file and file.filename:
                filename = secure_filename(file.filename)
                # Generate unique filename
                unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
                # Save the file
                upload_folder = current_app.config['UPLOAD_FOLDER']
                file_path = os.path.join(upload_folder, unique_filename)
                file.save(file_path)
                # Store the relative URL
                image_url = f"/static/uploads/{unique_filename}"

        # Create the product
        product = Product.create(
            category_id=category_id,
            product_name=product_name,
            description=description,
            image=image_url,
            owner_id=user_id
        )

        if not product:
            flash('Failed to create product', 'error')
            return redirect(url_for('seller.create_product'))

        # Add product to inventory
        inventory_id = Inventory.create(user_id, product.id, quantity, unit_price)
        print(f"Inventory ID: {inventory_id}")

        if inventory_id is not None:
            flash('Product created and added to inventory', 'success')
            return redirect(url_for('seller.inventory'))
        else:
            flash('Product created but could not be added to inventory', 'warning')
            return redirect(url_for('seller.add_inventory'))

    # GET request - show the product creation form
    categories = {cat.id: cat.name for cat in Category.get_all()}

    return render_template(
        'seller/create_product.html',
        categories=categories
    )


# Modified edit_inventory route for seller.py that supports product editing

@bp.route('/inventory/edit/<int:inventory_id>', methods=['GET', 'POST'])
@seller_required
def edit_inventory(inventory_id):
    """Edit inventory item and product details if owner"""
    user_id = session['user_id']

    # Get inventory item with product details
    item = Inventory.get(inventory_id)

    if not item or item.seller_id != user_id:
        flash('Inventory item not found', 'error')
        return redirect(url_for('seller.inventory'))

    # Check if the current seller is also the product owner
    is_owner = (item.owner_id == user_id)

    # Get categories for product editing
    categories = Category.get_all() if is_owner else None

    if request.method == 'POST':
        # Always process inventory updates
        quantity = request.form.get('quantity', type=int)
        unit_price = request.form.get('unit_price', type=float)

        # Validate inventory inputs
        if quantity is None or unit_price is None:
            flash('All inventory fields are required', 'error')
            return redirect(url_for('seller.edit_inventory', inventory_id=inventory_id))

        if quantity < 0:
            flash('Quantity cannot be negative', 'error')
            return redirect(url_for('seller.edit_inventory', inventory_id=inventory_id))

        if unit_price <= 0:
            flash('Price must be greater than zero', 'error')
            return redirect(url_for('seller.edit_inventory', inventory_id=inventory_id))

        # If seller is also the product owner, process product updates
        if is_owner:
            product_name = request.form.get('product_name')
            category_id = request.form.get('category_id', type=int)
            description = request.form.get('description')

            # Validate product inputs
            if not product_name or not description or not category_id:
                flash('All product fields are required', 'error')
                return redirect(url_for('seller.edit_inventory', inventory_id=inventory_id))

            # Handle image upload if provided
            image_url = None
            if 'product_image' in request.files:
                file = request.files['product_image']
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    # Generate unique filename
                    unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
                    # Save the file
                    upload_folder = current_app.config['UPLOAD_FOLDER']
                    file_path = os.path.join(upload_folder, unique_filename)
                    file.save(file_path)
                    # Store the relative URL
                    image_url = unique_filename

            # Update product details if owner
            product_updated = Product.update(
                product_id=item.product_id,
                category_id=category_id,
                product_name=product_name,
                description=description,
                image=image_url if image_url else None  # Only update if new image was uploaded
            )

            if not product_updated:
                flash('Failed to update product details', 'error')
                return redirect(url_for('seller.edit_inventory', inventory_id=inventory_id))

        # Update inventory details
        result = Inventory.update(inventory_id, user_id, quantity, unit_price)

        if result:
            flash('Inventory updated successfully', 'success')
            return redirect(url_for('seller.inventory'))
        else:
            flash('Failed to update inventory', 'error')
            return redirect(url_for('seller.edit_inventory', inventory_id=inventory_id))

    # GET request - show form
    return render_template(
        'seller/edit_inventory.html',
        item=item,
        is_owner=is_owner,
        categories=categories
    )


@bp.route('/inventory/delete/<int:inventory_id>', methods=['POST'])
@seller_required
def delete_inventory(inventory_id):
    """Remove a product from inventory"""
    user_id = session['user_id']

    result = Inventory.delete(inventory_id, user_id)

    if result:
        flash('Product removed from inventory', 'success')
    else:
        flash('Failed to remove product from inventory', 'error')

    return redirect(url_for('seller.inventory'))


@bp.route('/orders')
@seller_required
def orders():
    """View orders to be fulfilled"""
    user_id = session['user_id']

    page = request.args.get('page', 1, type=int)
    status = request.args.get('status')

    # Items per page
    per_page = 10

    # Get orders with pagination
    orders_list = Order.get_for_seller(
        user_id,
        limit=per_page,
        offset=(page - 1) * per_page,
        status=status
    )

    # Get total count for pagination
    total_orders = Order.count_for_seller(user_id, status=status)

    return render_template(
        'seller/orders.html',
        orders=orders_list,
        current_status=status,
        pagination={
            'page': page,
            'per_page': per_page,
            'total': total_orders,
            'pages': (total_orders + per_page - 1) // per_page
        }
    )


@bp.route('/orders/<int:order_id>')
@seller_required
def order_details(order_id):
    """View details of a specific order"""
    user_id = session['user_id']

    # Get the order
    order = Order.get(order_id)

    if not order:
        flash('Order not found', 'error')
        return redirect(url_for('seller.orders'))

    # Filter items to only show this seller's items
    seller_items = [item for item in order.items if item.seller_id == user_id]

    # change image path
    for item in seller_items:
        if item.image:
            item.image = f"/static/uploads/{item.image}"
        else:
            item.image = "/static/uploads/image-default.png"

    if not seller_items:
        flash('No items in this order belong to you', 'error')
        return redirect(url_for('seller.orders'))

    # Replace order items with filtered list
    order.items = seller_items

    print(order.items[0].status)

    return render_template(
        'seller/order_details.html',
        order=order
    )


@bp.route('/orders/fulfill/<int:order_item_id>', methods=['POST'])
@seller_required
def fulfill_item(order_item_id):
    """Mark an order item as fulfilled"""
    user_id = session['user_id']

    success, error = OrderItem.fulfill(order_item_id, user_id)

    if success:
        flash('Item marked as fulfilled', 'success')
    else:
        flash(f'Failed to fulfill item: {error}', 'error')

    # Get the order ID to redirect back to order details
    item = OrderItem.get(order_item_id)
    if item:
        return redirect(url_for('seller.order_details', order_id=item.order_id))
    else:
        return redirect(url_for('seller.orders'))


# Add this to your seller.py file

@bp.route('/analytics')
@seller_required
def product_analytics():
    """Product analytics dashboard for sellers"""
    user_id = session['user_id']

    # Get date ranges for filtering
    from datetime import datetime, timedelta
    today = datetime.now()

    # Default is last 30 days
    days = request.args.get('days', 30, type=int)
    start_date = today - timedelta(days=days)

    # Get sales data by category
    category_sales = current_app.db.execute('''
        SELECT pc.category_name, SUM(op.quantity) as sold_quantity, 
            SUM(op.quantity * op.price) as total_sales,
            COUNT(DISTINCT o.order_id) as order_count
        FROM Orders_Products op
        JOIN Orders o ON op.order_id = o.order_id
        JOIN Products p ON op.product_id = p.product_id
        JOIN Products_Categories pc ON p.category_id = pc.category_id
        WHERE op.seller_id = :seller_id
        AND o.order_date >= :start_date
        GROUP BY pc.category_name
        ORDER BY total_sales DESC
    ''', seller_id=user_id, start_date=start_date)

    # Get sales data by product
    product_sales = current_app.db.execute('''
        SELECT p.product_name, pc.category_name,
            SUM(op.quantity) as sold_quantity, 
            SUM(op.quantity * op.price) as total_sales,
            COUNT(DISTINCT o.order_id) as order_count
        FROM Orders_Products op
        JOIN Orders o ON op.order_id = o.order_id
        JOIN Products p ON op.product_id = p.product_id
        JOIN Products_Categories pc ON p.category_id = pc.category_id
        WHERE op.seller_id = :seller_id
        AND o.order_date >= :start_date
        GROUP BY p.product_name, pc.category_name
        ORDER BY total_sales DESC
        LIMIT 10
    ''', seller_id=user_id, start_date=start_date)

    # Get sales trend over time (by day/week depending on date range)
    if days <= 30:
        # Daily data for shorter periods
        time_series = current_app.db.execute('''
            SELECT DATE(o.order_date) as date, 
                SUM(op.quantity) as sold_quantity,
                SUM(op.quantity * op.price) as total_sales
            FROM Orders_Products op
            JOIN Orders o ON op.order_id = o.order_id
            WHERE op.seller_id = :seller_id
            AND o.order_date >= :start_date
            GROUP BY DATE(o.order_date)
            ORDER BY date
        ''', seller_id=user_id, start_date=start_date)
    else:
        # Weekly data for longer periods
        time_series = current_app.db.execute('''
            SELECT DATE_TRUNC('week', o.order_date) as week_start,
                SUM(op.quantity) as sold_quantity,
                SUM(op.quantity * op.price) as total_sales
            FROM Orders_Products op
            JOIN Orders o ON op.order_id = o.order_id
            WHERE op.seller_id = :seller_id
            AND o.order_date >= :start_date
            GROUP BY week_start
            ORDER BY week_start
        ''', seller_id=user_id, start_date=start_date)

    # Get inventory status vs. sales rate (to identify potential stock issues)
    stock_vs_sales = current_app.db.execute('''
        SELECT p.product_name, i.quantity as current_stock,
            COALESCE(SUM(op.quantity), 0) as units_sold,
            CASE 
                WHEN COALESCE(SUM(op.quantity), 0) = 0 THEN NULL
                ELSE i.quantity::float / (SUM(op.quantity)::float / :days)
            END as days_of_stock_left
        FROM Inventory i
        JOIN Products p ON i.product_id = p.product_id
        LEFT JOIN Orders_Products op ON i.product_id = op.product_id
            AND op.seller_id = i.seller_id
            AND op.order_id IN (
                SELECT order_id FROM Orders 
                WHERE order_date >= :start_date
            )
        WHERE i.seller_id = :seller_id
        GROUP BY p.product_name, i.quantity
        ORDER BY days_of_stock_left ASC NULLS LAST
        LIMIT 10
    ''', seller_id=user_id, start_date=start_date, days=days)

    # Get unfulfilled order count by category
    unfulfilled_by_category = current_app.db.execute('''
        SELECT pc.category_name, COUNT(*) as unfulfilled_count
        FROM Orders_Products op
        JOIN Products p ON op.product_id = p.product_id
        JOIN Products_Categories pc ON p.category_id = pc.category_id
        WHERE op.seller_id = :seller_id
        AND op.status = 'Unfulfilled'
        GROUP BY pc.category_name
        ORDER BY unfulfilled_count DESC
    ''', seller_id=user_id)

    # Format data for charts
    category_data = {
        'labels': [row[0] for row in category_sales],
        'quantities': [row[1] for row in category_sales],
        'sales': [float(row[2]) for row in category_sales]
    }

    time_series_data = {
        'labels': [row[0].strftime('%Y-%m-%d') if hasattr(row[0], 'strftime') else str(row[0]) for row in time_series],
        'quantities': [row[1] for row in time_series],
        'sales': [float(row[2]) for row in time_series]
    }

    product_data = {
        'labels': [row[0] for row in product_sales],
        'categories': [row[1] for row in product_sales],
        'quantities': [row[2] for row in product_sales],
        'sales': [float(row[3]) for row in product_sales]
    }

    stock_data = {
        'products': [row[0] for row in stock_vs_sales],
        'current_stock': [row[1] for row in stock_vs_sales],
        'units_sold': [row[2] for row in stock_vs_sales],
        'days_left': [float(row[3]) if row[3] is not None else None for row in stock_vs_sales]
    }

    unfulfilled_data = {
        'categories': [row[0] for row in unfulfilled_by_category],
        'counts': [row[1] for row in unfulfilled_by_category]
    }

    return render_template(
        'seller/analytics.html',
        days=days,
        category_data=category_data,
        time_series_data=time_series_data,
        product_data=product_data,
        stock_data=stock_data,
        unfulfilled_data=unfulfilled_data,
        product_sales=product_sales,
        stock_vs_sales=stock_vs_sales
    )