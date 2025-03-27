from flask import render_template, request
from flask_login import current_user
import datetime

from .models.orders import Order
from .models.product import Product

from flask import Blueprint

bp = Blueprint('index', __name__)


@bp.route('/')
def index():
    # Get search parameters
    search_query = request.args.get('search', '')

    # Get all available products for sale:
    if search_query:
        products = Product.search(query=search_query)
    else:
        products = Product.get_all(True)

    for product in products:
        inventory_items = product.get_inventory_items()
        if inventory_items:
            # Get the lowest price
            product.price = min(item.unit_price for item in inventory_items)
        else:
            product.price = 0.00  # No inventory available

    # Find the products current user has bought:
    if current_user.is_authenticated:
        purchases = Order.get_for_buyer(current_user.id)
    else:
        purchases = None

    return render_template('index.html',
                           avail_products=products,
                           purchase_history=purchases,
                           search_query=search_query)