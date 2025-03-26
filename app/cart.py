# app/cart.py
from flask import Blueprint, request, redirect, url_for, flash, render_template
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


@bp.route("/view")
@login_required
def view_cart():
    cart_items = Cart.get_cart_items(current_user.id)
    total_cart_value = sum(item[7] for item in cart_items)
    return render_template("cart.html", cart_items=cart_items, total_cart_value=total_cart_value)


@bp.route("/remove", methods=["POST"])
@login_required
def remove_from_cart():
    product_id = request.form.get("product_id")
    seller_id = request.form.get("seller_id")
    
    if not product_id or not seller_id:
        flash("Invalid removal request", "danger")
        return redirect(url_for('cart.view_cart'))
    
    try:
        result = app.db.execute('''
        DELETE FROM Cart_Products 
        WHERE user_id = :user_id 
        AND product_id = :product_id 
        AND seller_id = :seller_id
        ''', user_id=current_user.id, product_id=product_id, seller_id=seller_id)
        
        flash("Item removed from cart", "success")
    except Exception as e:
        print(f"Error removing from cart: {e}")
        flash("Error removing item", "danger")
    
    return redirect(url_for('cart.view_cart'))