# app/cart.py
from flask import Blueprint, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.cart import Cart

bp = Blueprint("cart", __name__, url_prefix="/cart")

@bp.route("/add", methods=["POST"])
@login_required
def add_to_cart():
    product_id = request.form.get("product_id")
    seller_id = request.form.get("seller_id")
    quantity = request.form.get("quantity", type=int)

    if not product_id or not seller_id or quantity <= 0:
        flash("Invalid form submission", "danger")
        return redirect(request.referrer)

    success = Cart.add_to_cart(current_user.id, product_id, seller_id, quantity)
    if success:
        flash("Added to cart!", "success")
    else:
        flash("Error adding to cart", "danger")

    return redirect(request.referrer)
