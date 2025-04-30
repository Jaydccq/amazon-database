from flask import Blueprint, request, redirect, url_for, flash, render_template, session, current_app as app
from flask_login import login_required, current_user
from app.models.cart import Cart
from app.models.inventory import Inventory

bp = Blueprint("cart", __name__, url_prefix="/cart")

@bp.route('/cart/checkout', methods=['POST'])
@login_required
def checkout():
    success, info = Cart.checkout_cart(current_user.id)
    if success:
        flash("Checkout successful!")
        return redirect(url_for('index.index'))
    else:
        flash("Checkout failed. "+ info)
    return redirect(url_for('index.index'))

@bp.route("/", methods=["GET"])
@login_required
def view_cart():
    try:
        cart_items = Cart.get_cart_items(current_user.id)

        total_cart_value = sum(item[7] for item in cart_items) if cart_items else 0

        return render_template('cart.html',
                               cart_items=cart_items,
                               total_cart_value=total_cart_value)
    except Exception as e:
        print(f"Error retrieving cart: {e}")
        flash("An error occurred while retrieving your cart", "danger")
        return redirect(url_for('index.index'))


@bp.route("/add", methods=["POST"])
@login_required
def add_to_cart():
    product_id = request.form.get("product_id")
    seller_id = request.form.get("seller_id")
    quantity = int(request.form.get("quantity", 1))

    if not product_id or not seller_id:
        flash("Invalid product information", "danger")
        return redirect(request.referrer or url_for('index.index'))

    try:
        inventory = Inventory.get_by_seller_and_product(seller_id, product_id)
        print(f"Inventory: {inventory}")
        print("seller_id:", seller_id)
        print("product_id:", product_id)
        if not inventory or inventory.quantity < quantity:
            flash("This product is out of stock or not available in the requested quantity", "warning")
            return redirect(request.referrer or url_for('index.index'))

        # Add to cart
        cart_id = Cart.add_to_cart(current_user.id, product_id, seller_id, quantity)

        if cart_id:
            flash("Product added to cart", "success")
        else:
            flash("Failed to add product to cart", "danger")

    except Exception as e:
        print(f"Error adding to cart: {e}")
        flash("An error occurred while adding to cart", "danger")

    return redirect(request.referrer or url_for('index.index'))


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


@bp.route("/update", methods=["POST"])
@login_required
def update_cart():
    product_id = request.form.get("product_id")
    seller_id = request.form.get("seller_id")
    quantity = int(request.form.get("quantity", 1))

    if not product_id or not seller_id or quantity < 1:
        flash("Invalid update request", "danger")
        return redirect(url_for('cart.view_cart'))

    try:
        # check availability
        inventory = Inventory.get_by_seller_and_product(seller_id, product_id)
        if not inventory or inventory.quantity < quantity:
            flash("The requested quantity is not available", "warning")
            return redirect(url_for('cart.view_cart'))

        # Get cart_id
        cart_rows = app.db.execute('''
        SELECT cart_id FROM Carts 
        WHERE user_id = :user_id
        ''', user_id=current_user.id)

        if not cart_rows:
            flash("Cart not found", "danger")
            return redirect(url_for('cart.view_cart'))

        cart_id = cart_rows[0][0]

        app.db.execute('''
        UPDATE Cart_Products
        SET quantity = :quantity
        WHERE cart_id = :cart_id
        AND product_id = :product_id
        AND seller_id = :seller_id
        ''', quantity=quantity, cart_id=cart_id, product_id=product_id, seller_id=seller_id)

        flash("Cart updated successfully", "success")
    except Exception as e:
        print(f"Error updating cart: {e}")
        flash("Error updating cart", "danger")

    return redirect(url_for('cart.view_cart'))