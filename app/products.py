# app/products.py
from flask import Blueprint, render_template, jsonify, request, abort
from flask_login import current_user
from app.models.product import Product
from app.models.review import Review
from app.models.inventory import Inventory
from flask import Blueprint, render_template, jsonify, request, abort, current_app
bp = Blueprint("product", __name__, url_prefix="/products")

@bp.route("/<int:product_id>")
def product_detail(product_id):
    product = Product.get(product_id)
    if not product:
        abort(404, description="Product not found")

    inventory_items = Inventory.get_sellers_for_product(product_id)
    print(f"DEBUG: Original product.image from DB: {product.image}")
    product.inventory = inventory_items
    product.image = f"/static/uploads/{product.image}"
    print(f"DEBUG: Original product.image from DB: {product.image}")
    print(product.image)

    reviews = Review.get_product_review(product_id)
    reviews = Review.get_product_review(product_id)


    return render_template("product_detail.html",
                           product=product,
                           reviews=reviews)


@bp.route("/api/<int:product_id>")
def product_api(product_id):
    product = Product.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    return jsonify(product.to_dict())


@bp.route("/expensive/<int:k>")
def top_expensive_products(k):
    products = Product.get_top_k_expensive(k)
    return render_template("top_expensive.html", products=products)

@bp.route("/api/expensive/<int:k>")
def api_top_expensive_products(k):
    products = Product.get_top_k_expensive(k)
    return jsonify([{
        'id': product.id,
        'name': product.name,
        'description': product.description,
        'category_id': product.category_id,
        'category_name': product.category_name,
        'price': float(product.price) if product.price else None,
        'owner_id': product.owner_id,
        'owner_name': product.owner_name,
        'avg_rating': float(product.avg_rating) if product.avg_rating else 0,
        'review_count': product.review_count
    } for product in products])



@bp.route("/category/<int:category_id>")
def category(category_id):
    """Display products by category"""
    # Get category information
    # Use current_app proxy to access the db attached to the app instance
    category_data = current_app.db.execute('''
        SELECT category_id, category_name
        FROM Products_Categories
        WHERE category_id = :category_id
    ''', category_id=category_id)

    if not category_data:
        abort(404, description="Category not found")

    category_name = category_data[0][1] # Access the name correctly

    # Get sorting parameters
    sort_by = request.args.get('sort_by', 'name')
    sort_dir = request.args.get('sort_dir', 'asc')
    page = request.args.get('page', 1, type=int)
    per_page = 12  # Number of products per page

    # Build the query based on sorting parameters
    query = '''
        SELECT p.product_id, p.category_id, p.product_name, p.description,
               p.image, p.owner_id, p.created_at, p.updated_at,
               c.category_name, CONCAT(a.first_name, ' ', a.last_name) AS owner_name,
               COALESCE(AVG(r.rating), 0) as avg_rating,
               COUNT(r.review_id) as review_count,
               MIN(i.unit_price) as min_price
        FROM Products p
        JOIN Products_Categories c ON p.category_id = c.category_id
        JOIN Accounts a ON p.owner_id = a.user_id
        LEFT JOIN Reviews_Feedbacks r ON p.product_id = r.product_id
        LEFT JOIN Inventory i ON p.product_id = i.product_id
        WHERE p.category_id = :category_id
        GROUP BY p.product_id, c.category_name, a.first_name, a.last_name
    '''

    # Add sorting
    if sort_by == 'price':
        query += " ORDER BY min_price"
    elif sort_by == 'rating':
        query += " ORDER BY avg_rating"
    elif sort_by == 'newest':
        query += " ORDER BY p.created_at"
    else:  # default to name
        query += " ORDER BY p.product_name"

    # Add sort direction
    query += " DESC" if sort_dir.lower() == 'desc' else " ASC"

    # Get total count first (for pagination)
    count_query = '''
        SELECT COUNT(DISTINCT p.product_id)
        FROM Products p
        WHERE p.category_id = :category_id
    '''
    # Use current_app proxy
    total_count_result = current_app.db.execute(count_query, category_id=category_id)
    total_count = total_count_result[0][0] if total_count_result and total_count_result[0] else 0


    # Add pagination
    query += " LIMIT :limit OFFSET :offset"
    offset = (page - 1) * per_page

    # Execute the query - Use current_app proxy
    rows = current_app.db.execute(query, category_id=category_id, limit=per_page, offset=offset)

    # Create Product objects
    products = []
    for row in rows if rows else []: # Check if rows is not None
        # Adjust index based on your Product model constructor if needed
        # Assuming Product needs: product_id, category_id, product_name, description, image, owner_id, created_at, updated_at, category_name, owner_name, avg_rating, review_count
        product_data = row[:-1] # Exclude min_price
        product = Product(*product_data)
        product.price = row[-1] if row else None # Add price separately
        products.append(product)


    # Calculate pagination values
    total_pages = (total_count + per_page - 1) // per_page
    has_prev = page > 1
    has_next = page < total_pages

    # Get subcategories if any (assuming you might have a hierarchy)
    # Use current_app proxy
    subcategories = current_app.db.execute('''
        SELECT category_id, category_name
        FROM Products_Categories
        WHERE category_id = :category_id
        ORDER BY category_name
    ''', category_id=category_id)

    # Return the template with data
    return render_template('category.html',
                           category_id=category_id,
                           category_name=category_name,
                           products=products,
                           subcategories=subcategories if subcategories else [],
                           sort_by=sort_by,
                           sort_dir=sort_dir,
                           page=page,
                           total_pages=total_pages,
                           has_prev=has_prev,
                           has_next=has_next,
                           per_page=per_page,
                           total_count=total_count)