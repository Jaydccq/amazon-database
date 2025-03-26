from flask import Blueprint,render_template, request
from flask_login import current_user
from app.models.product import Product,Category
import datetime

from .models.orders import Order

bp = Blueprint('index', __name__)


@bp.route('/')
def index():
    sort_by = request.args.get('sort_by')           # sort type
    k = request.args.get('k', type=int)              # top k
    category_id = request.args.get('category_id')    # category filter

    # Get all products and filter
    products = Product.get_all_with_min_price()

    if category_id:
        products = [p for p in products if str(p.get('category_id')) == category_id]

    # sort
    if sort_by == 'price_asc':
        products = sorted(products, key=lambda x: x['price'])
    elif sort_by == 'price_desc':
        products = sorted(products, key=lambda x: x['price'], reverse=True)

    # limit
    if k:
        products = products[:k]

    # get purchase history if logged in
    purchases = Order.get_for_buyer(current_user.id) if current_user.is_authenticated else None
    categories = Category.get_all()

    return render_template('index.html',
                           avail_products=products,
                           purchase_history=purchases,
                           sort_by=sort_by,
                           k=k,
                           categories=categories,
                           category_id=int(category_id) if category_id else None)
