from flask import Blueprint, request, redirect, url_for, flash, render_template
from flask_login import login_required, current_user
from app.models.cart import Cart
from app.models.inventory import Inventory
from flask import current_app as app # For logger

bp = Blueprint('cart', __name__, url_prefix='/cart')

@bp.route('/checkout', methods=['POST'])
@login_required
def checkout():
    # Checkout logic in model
    success, info = Cart.checkout_cart(current_user.id)
    if success:
        flash(info, "success")
        return redirect(url_for('index.index'))
    else:
        flash(f"Checkout failed: {info}", "danger")
        return redirect(url_for('cart.view_cart')) # Back to cart


@bp.route("/", methods=["GET"])
@login_required
def view_cart():
    try:
        # Get both cart sections
        cart_data = Cart.get_cart_items(current_user.id)
        in_cart_items = cart_data.get('in_cart', [])
        saved_items = cart_data.get('saved_for_later', [])

        # Calculate total from 'in_cart'
        total_cart_value = sum(item[7] for item in in_cart_items)

        print(f"DEBUG: In cart items passed to template: {in_cart_items}")  # <-- 查看传递给模板的数据
        print(f"DEBUG: Saved items passed to template: {saved_items}")  # <-- 查看传递给模板的数据

        return render_template('cart.html',
                               in_cart_items=in_cart_items,
                               saved_items=saved_items,
                               total_cart_value=total_cart_value)
    except Exception as e:
        app.logger.error(f"Error retrieving cart view user {current_user.id}: {e}", exc_info=True)
        flash("Error retrieving cart.", "danger")
        return redirect(url_for('index.index'))


@bp.route("/add", methods=["POST"])
@login_required
def add_to_cart():
    product_id = request.form.get("product_id")
    seller_id = request.form.get("seller_id")
    try:
        quantity = int(request.form.get("quantity", 1))
        if quantity < 1:
            flash("Quantity must be positive.", "warning")
            return redirect(request.referrer or url_for('index.index'))
    except ValueError:
        flash("Invalid quantity.", "danger")
        return redirect(request.referrer or url_for('index.index'))

    if not product_id or not seller_id:
        flash("Invalid product info.", "danger")
        return redirect(request.referrer or url_for('index.index'))

    try:
        # Check basic stock availability
        inventory = Inventory.get_by_seller_and_product(seller_id, product_id)
        if not inventory:
             flash("Product unavailable from seller.", "warning")
             return redirect(request.referrer or url_for('index.index'))
        if inventory.quantity <= 0:
             flash("Product out of stock.", "warning")
             return redirect(request.referrer or url_for('index.index'))

        # Add via model method
        success = Cart.add_to_cart(current_user.id, product_id, seller_id, quantity)

        if success:
            flash("Product added to cart.", "success")
        else:
            flash("Failed adding product.", "danger")

    except Exception as e:
        app.logger.error(f"Error in add_to_cart route user {current_user.id}: {e}", exc_info=True)
        flash("Error adding item.", "danger")

    return redirect(request.referrer or url_for('index.index'))


@bp.route("/remove", methods=["POST"])
@login_required
def remove_from_cart():
    # Removes item regardless of status
    product_id = request.form.get("product_id")
    seller_id = request.form.get("seller_id")

    if not product_id or not seller_id:
        flash("Invalid remove request.", "danger")
        return redirect(url_for('cart.view_cart'))

    try:
        cart_id = Cart._get_cart_id(current_user.id) # Use model helper
        if not cart_id:
            flash("Cart not found.", "danger")
            return redirect(url_for('cart.view_cart'))

        # Delete the specific item
        result = app.db.execute('''
            DELETE FROM Cart_Products
            WHERE cart_id = :cart_id
            AND product_id = :product_id
            AND seller_id = :seller_id
            ''', cart_id=cart_id, product_id=product_id, seller_id=seller_id, modify=True)

        if result is not None: # Check if deleted
             flash("Item removed from cart.", "success")
        else:
             flash("Item not removed.", "warning")

    except Exception as e:
        app.logger.error(f"Error removing item (pid:{product_id}, sid:{seller_id}) user {current_user.id}: {e}", exc_info=True)
        flash("Error removing item.", "danger")

    return redirect(url_for('cart.view_cart'))


@bp.route("/update", methods=["POST"])
@login_required
def update_cart():
    # Updates quantity for 'in_cart' items
    product_id = request.form.get("product_id")
    seller_id = request.form.get("seller_id")
    try:
        quantity = int(request.form.get("quantity", 1))
        if quantity < 1:
            flash("Quantity must be positive.", "danger")
            return redirect(url_for('cart.view_cart'))
    except ValueError:
        flash("Invalid quantity.", "danger")
        return redirect(url_for('cart.view_cart'))

    if not product_id or not seller_id:
        flash("Invalid update request.", "danger")
        return redirect(url_for('cart.view_cart'))

    try:
        # Check stock before update
        inventory = Inventory.get_by_seller_and_product(seller_id, product_id)
        if not inventory or inventory.quantity < quantity:
            available = inventory.quantity if inventory else 0
            flash(f"Only {available} in stock.", "warning")
            return redirect(url_for('cart.view_cart'))

        cart_id = Cart._get_cart_id(current_user.id)
        if not cart_id:
            flash("Cart not found.", "danger")
            return redirect(url_for('cart.view_cart'))

        # Update quantity if status 'in_cart'
        result = app.db.execute('''
            UPDATE Cart_Products
            SET quantity = :quantity
            WHERE cart_id = :cart_id
            AND product_id = :product_id
            AND seller_id = :seller_id
            AND status = 'in_cart' -- <<< Only update 'in_cart'
            ''', quantity=quantity, cart_id=cart_id, product_id=product_id, seller_id=seller_id, modify=True)

        if result is not None: # Check if updated
            flash("Cart updated.", "success")
        else:
            flash("Could not update quantity.", "warning")

    except Exception as e:
        app.logger.error(f"Error updating cart (pid:{product_id}, sid:{seller_id}) user {current_user.id}: {e}", exc_info=True)
        flash("Error updating cart.", "danger")

    return redirect(url_for('cart.view_cart'))


@bp.route("/save_for_later", methods=["POST"])
@login_required
def save_for_later():
    """ Moves item from cart to saved list """
    product_id = request.form.get("product_id")
    seller_id = request.form.get("seller_id")

    if not product_id or not seller_id:
        flash("Invalid request.", "danger")
        return redirect(url_for('cart.view_cart'))

    # Call model method
    success = Cart.move_to_saved(current_user.id, product_id, seller_id)
    if success:
        flash("Item saved for later.", "success")
    else:
        flash("Could not save item.", "danger")

    return redirect(url_for('cart.view_cart'))


@bp.route("/move_to_cart", methods=["POST"])
@login_required
def move_to_cart_route():
    """ Moves item from saved list to cart """
    product_id = request.form.get("product_id")
    seller_id = request.form.get("seller_id")

    if not product_id or not seller_id:
        flash("Invalid request.", "danger")
        return redirect(url_for('cart.view_cart'))

    # Optional: Check stock before move
    inventory = Inventory.get_by_seller_and_product(seller_id, product_id)
    if not inventory or inventory.quantity <= 0:
        flash("Item out of stock.", "warning")
        return redirect(url_for('cart.view_cart'))

    # Call model method
    success = Cart.move_to_cart(current_user.id, product_id, seller_id)
    if success:
        flash("Item moved to cart.", "success")
    else:
        flash("Could not move item.", "danger")

    return redirect(url_for('cart.view_cart'))