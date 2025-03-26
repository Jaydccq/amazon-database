# app/cart.py
from flask import Blueprint, request, redirect, url_for, flash, render_template, current_app as app
from flask_login import login_required, current_user
from app.models.cart import Cart

bp = Blueprint("cart", __name__, url_prefix="/cart")


@bp.route("/remove", methods=["POST"])
@login_required
def remove_from_cart():
    product_id = request.form.get("product_id")
    seller_id = request.form.get("seller_id")

    if not product_id or not seller_id:
        flash("Invalid removal request", "danger")
        return redirect(url_for('cart.view_cart'))

    try:
        cart_rows = app.db.execute('''
        SELECT cart_id FROM Carts 
        WHERE user_id = :user_id
        ''', user_id=current_user.id)

        if not cart_rows:
            flash("Cart not found", "danger")
            return redirect(url_for('cart.view_cart'))

        cart_id = cart_rows[0][0]

        result = app.db.execute('''
        DELETE FROM Cart_Products 
        WHERE cart_id = :cart_id 
        AND product_id = :product_id 
        AND seller_id = :seller_id
        ''', cart_id=cart_id, product_id=product_id, seller_id=seller_id)

        flash("Item removed from cart", "success")
    except Exception as e:
        print(f"Error removing from cart: {e}")
        flash("Error removing item", "danger")

    return redirect(url_for('cart.view_cart'))