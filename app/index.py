from flask import render_template
from flask_login import current_user
from app.models.product import Product
import datetime

from .models.orders import Order
from .models.product import Product

from flask import Blueprint
bp = Blueprint('index', __name__)


@bp.route('/')
def index():
    avail_products = Product.get_all_with_min_price()

    if current_user.is_authenticated:
        purchases = Order.get_for_buyer(current_user.id)
    else:
        purchases = None

    return render_template("index.html",
                           avail_products=avail_products,
                           purchase_history=purchases)

