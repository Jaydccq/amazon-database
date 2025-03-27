# index.py
from flask import render_template, request
from flask_login import current_user
import datetime

from .models.orders import Order
from .models.product import Product

from flask import Blueprint

bp = Blueprint('index', __name__)


@bp.route('/')
def index():
    search_query = request.args.get('search', '')

    filter_type = request.args.get('filter', '')
    top_k = request.args.get('top_k', type=int, default=5) # Default top 5
    sort_by = request.args.get('sort_by', 'name')  # Default sorting by name
    sort_dir = request.args.get('sort_dir', 'asc')  # Default ascending order

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
                    product.price = 0.00  # Default price

            products = sorted(all_products,
                              key=lambda p: p.price if p.price is not None else 0.0,
                              reverse=(sort_dir == 'desc'))
        else:
            products = Product.search(query=search_query,
                                      sort_by=sort_by,
                                      sort_dir=sort_dir)

    for product in products:
        if not hasattr(product, 'price') or product.price is None:
            inventory_items = product.get_inventory_items()
            if inventory_items:
                product.price = min(item.unit_price for item in inventory_items)
            else:
                product.price = 0.00  # Default price value

    if current_user.is_authenticated:
        purchases = Order.get_for_buyer(current_user.id)
    else:
        purchases = None

    return render_template('index.html',
                           avail_products=products,
                           purchase_history=purchases,
                           search_query=search_query,
                           filter_type=filter_type,
                           top_k=top_k,
                           sort_by=sort_by,
                           sort_dir=sort_dir)