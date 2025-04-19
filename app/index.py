# index.py
from flask import render_template, request
from flask_login import login_required, current_user
import datetime

from .models.orders import Order
from .models.product import Product

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
    orders = Order.get_for_buyer(current_user.id, limit=100)
    return render_template('purchase_history.html', orders=orders)


