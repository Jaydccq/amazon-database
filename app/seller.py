from flask import Blueprint, render_template, request, redirect, url_for
from flask import flash, session, current_app, jsonify
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

    # GET request - show form with available products

    # GET request - show form with available products

    # Get search parameters
    search_query = request.args.get('search', '')
    current_category = request.args.get('category_id', '')

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

    # Get categories for grouping products
    categories = {cat.id: cat.name for cat in Category.get_all()}

    # Make sure Product objects have the right attributes for the template
    for p in available_products:
        # Add id and name attributes if they don't exist
        if not hasattr(p, 'id'):
            p.id = p.product_id
        if not hasattr(p, 'name'):
            p.name = p.product_name

    return render_template(
        'seller/add_inventory.html',
        available_products=available_products,
        categories=categories,
        search_query=search_query,
        current_category=current_category
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


@bp.route('/inventory/edit/<int:inventory_id>', methods=['GET', 'POST'])
@seller_required
def edit_inventory(inventory_id):
    """Edit inventory item"""
    user_id = session['user_id']

    # Get inventory item
    item = Inventory.get(inventory_id)

    if not item or item.seller_id != user_id:
        flash('Inventory item not found', 'error')
        return redirect(url_for('seller.inventory'))

    if request.method == 'POST':
        quantity = request.form.get('quantity', type=int)
        unit_price = request.form.get('unit_price', type=float)

        # Validate inputs
        if quantity is None or unit_price is None:
            flash('All fields are required', 'error')
            return redirect(url_for('seller.edit_inventory', inventory_id=inventory_id))

        if quantity < 0:
            flash('Quantity cannot be negative', 'error')
            return redirect(url_for('seller.edit_inventory', inventory_id=inventory_id))

        if unit_price <= 0:
            flash('Price must be greater than zero', 'error')
            return redirect(url_for('seller.edit_inventory', inventory_id=inventory_id))

        # Update inventory
        result = Inventory.update(inventory_id, user_id, quantity, unit_price)

        if result:
            flash('Inventory updated', 'success')
            return redirect(url_for('seller.inventory'))
        else:
            flash('Failed to update inventory', 'error')
            return redirect(url_for('seller.edit_inventory', inventory_id=inventory_id))

    # GET request - show form
    return render_template(
        'seller/edit_inventory.html',
        item=item
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