from flask import Blueprint, render_template, request
from flask_login import current_user
from app.models.product import Product, Category
from app.models.orders import Order

bp = Blueprint('index', __name__)

@bp.route('/')
def index():
    sort_by = request.args.get('sort_by')
    try:
        k = int(request.args.get('k'))
    except (TypeError, ValueError):
        k = None
    print("[DEBUG] k =", k)
    category_id = request.args.get('category_id', type=int)

    categories = Category.get_all()

    all_products = Product.get_all_with_min_price(k=k)

    if category_id:
        all_products = [p for p in all_products if p.get('category_id') == category_id]

    if sort_by == 'price_asc':
        all_products = sorted(all_products, key=lambda x: x['price'])
    elif sort_by == 'price_desc':
        all_products = sorted(all_products, key=lambda x: x['price'], reverse=True)

    if k:
        all_products = all_products[:k]

    purchases = Order.get_for_buyer(current_user.id) if current_user.is_authenticated else None

    return render_template(
        'index.html',
        avail_products=all_products,
        purchase_history=purchases,
        sort_by=sort_by,
        k=k,
        categories=categories,
        category_id=category_id,
    )
