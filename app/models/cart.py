from flask import current_app as app
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class Cart:
    @staticmethod
    def add_to_cart(user_id, product_id, seller_id, quantity):
        try:
            # Find or create cart
            cart_rows = app.db.execute('''
            SELECT cart_id FROM Carts WHERE user_id = :user_id
            ''', user_id=user_id)

            if not cart_rows:
                app.db.execute('''
                INSERT INTO Carts (user_id, created_at, updated_at)
                VALUES (:user_id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ''', user_id=user_id)
                cart_rows = app.db.execute('''
                SELECT cart_id FROM Carts WHERE user_id = :user_id
                ''', user_id=user_id)
            cart_id = cart_rows[0][0]

            # Get current item price
            price_rows = app.db.execute('''
            SELECT unit_price FROM Inventory
            WHERE product_id = :product_id AND seller_id = :seller_id
            ''', product_id=product_id, seller_id=seller_id)

            if not price_rows:
                logger.warning("Attempted add with no price.")
                return None
            unit_price = price_rows[0][0]

            # Insert or update item
            # Handles conflicts, moves saved to cart
            result = app.db.execute('''
            INSERT INTO Cart_Products (cart_id, product_id, seller_id, quantity, price_at_addition, added_at, status)
            VALUES (:cart_id, :product_id, :seller_id, :quantity, :price, :added_at, 'in_cart')
            ON CONFLICT (cart_id, product_id, seller_id)
            DO UPDATE SET
                quantity = CASE
                               WHEN Cart_Products.status = 'saved_for_later' THEN :quantity -- Saved: set new quantity
                               ELSE Cart_Products.quantity + :quantity        -- In cart: increase quantity
                           END,
                price_at_addition = :price,
                added_at = :added_at,
                status = 'in_cart' -- Ensure status is 'in_cart'
            RETURNING cart_id
            ''', cart_id=cart_id, product_id=product_id, seller_id=seller_id,
                                    quantity=quantity, price=unit_price, added_at=datetime.utcnow())

            return result[0][0] if result else None
        except Exception as e:
            logger.error(f"Error adding to cart for user {user_id}: {e}", exc_info=True)
            return None

    @staticmethod
    def get_cart_items(user_id):
        items = {'in_cart': [], 'saved_for_later': []}
        try:
            result = app.db.execute('''
            SELECT
                    cp.product_id,
                    cp.seller_id,
                    cp.quantity,
                    p.product_name,
                    p.description,
                    p.image,
                    cp.price_at_addition as unit_price,
                    (cp.quantity * cp.price_at_addition) as total_price,
                    CONCAT(a.first_name, ' ', a.last_name) as seller_name,
                    p.owner_id
                FROM Cart_Products cp
                JOIN Carts c ON cp.cart_id = c.cart_id
                JOIN Products p ON cp.product_id = p.product_id
                JOIN Accounts a ON cp.seller_id = a.user_id
                WHERE c.user_id = :user_id
                ORDER BY cp.added_at DESC -- <<< REMOVED cp.status from ORDER BY
                ''',
                user_id=user_id)

            # Separate items by status
            for row in result:
                if row[10] == 'in_cart': # status is 'in_cart'
                    items['in_cart'].append(row)
                elif row[10] == 'saved_for_later': # status is 'saved_for_later'
                    items['saved_for_later'].append(row)

            return items
        except Exception as e:
            logger.error(f"Error getting cart items for user {user_id}: {e}", exc_info=True)
            return items # Return empty structure

    @staticmethod
    def _get_cart_id(user_id):
        """ Helper: find user's cart_id """
        cart_rows = app.db.execute('SELECT cart_id FROM Carts WHERE user_id = :user_id', user_id=user_id)
        return cart_rows[0][0] if cart_rows else None

    @staticmethod
    def update_item_status(user_id, product_id, seller_id, status):
        """ Updates item status in cart """
        cart_id = Cart._get_cart_id(user_id)
        if not cart_id:
            logger.warning(f"Update status fail: no cart for user {user_id}.")
            return False
        try:
            rows_affected = app.db.execute('''
                UPDATE Cart_Products
                SET status = :status
                WHERE cart_id = :cart_id
                AND product_id = :product_id
                AND seller_id = :seller_id
            ''', status=status, cart_id=cart_id, product_id=product_id, seller_id=seller_id, modify=True)
            logger.info(f"Updated status to '{status}' for item (pid:{product_id}, sid:{seller_id}) in cart {cart_id}. Rows affected: {rows_affected}")
            return rows_affected is not None and rows_affected > 0 # Check if update worked
        except Exception as e:
            logger.error(f"Error updating status to '{status}' for item (pid:{product_id}, sid:{seller_id}) in cart {cart_id}: {e}", exc_info=True)
            return False

    @staticmethod
    def move_to_saved(user_id, product_id, seller_id):
        """ Sets item status to saved """
        return Cart.update_item_status(user_id, product_id, seller_id, 'saved_for_later')

    @staticmethod
    def move_to_cart(user_id, product_id, seller_id):
        """ Sets item status to in_cart """
        return Cart.update_item_status(user_id, product_id, seller_id, 'in_cart')


    @staticmethod
    def checkout_cart(user_id):
        """ Processes 'in_cart' items for checkout """
        cart_id = Cart._get_cart_id(user_id)
        if not cart_id:
            return False, "Cart does not exist."

        try:
            # Get 'in_cart' items only
            cart_items = app.db.execute('''
                SELECT
                    cp.product_id,
                    cp.seller_id,
                    cp.quantity,
                    i.unit_price,
                    i.quantity as available_quantity
                FROM Cart_Products cp
                JOIN Inventory i ON cp.product_id = i.product_id AND cp.seller_id = i.seller_id
                WHERE cp.cart_id = :cart_id AND cp.status = 'in_cart' -- <<< Filter: in_cart only
                ''', cart_id=cart_id)

            if not cart_items:
                return False, "Your active cart is empty."

            # Check inventory stock
            logger.info("Checking inventory...")
            insufficient_items = []
            product_names = {}
            for item in cart_items:
                if item[0] not in product_names:
                     name_row = app.db.execute('SELECT product_name FROM Products WHERE product_id = :pid', pid=item[0])
                     product_names[item[0]] = name_row[0][0] if name_row else f"Product ID {item[0]}"

                if item[2] > item[4]: # quantity_cart > quantity_inventory
                    insufficient_items.append(f"{product_names[item[0]]} (Required: {item[2]}, In stock: {item[4]})")

            if insufficient_items:
                 return False, f"Insufficient stock: {', '.join(insufficient_items)}"


            # Check user balance
            total_amount = sum(item[2] * item[3] for item in cart_items) # quantity * price
            logger.info(f"Calculated total: {total_amount}")
            user_balance_row = app.db.execute('SELECT current_balance FROM Accounts WHERE user_id = :user_id', user_id=user_id)
            if not user_balance_row:
                return False, "Could not get balance."
            user_balance = user_balance_row[0][0]

            if user_balance < total_amount:
                return False, f"Insufficient balance: need ${total_amount:.2f}"

            # Start DB transaction
            logger.info("Begin checkout transaction...")
            app.db.execute('BEGIN')
            try:
                # Group items by seller
                sellers_items = {}
                for item in cart_items:
                    seller_id = item[1]
                    if seller_id not in sellers_items:
                        sellers_items[seller_id] = []
                    sellers_items[seller_id].append(item)

                order_ids = []
                # Create order per seller
                for seller_id, items in sellers_items.items():
                    seller_total = sum(it[2] * it[3] for it in items)
                    seller_num_products = sum(it[2] for it in items)

                    # Create Orders entry
                    order_rows = app.db.execute('''
                        INSERT INTO Orders (buyer_id, total_amount, num_products, order_date)
                        VALUES (:user_id, :total_amount, :num_products, CURRENT_TIMESTAMP)
                        RETURNING order_id
                        ''', user_id=user_id, total_amount=seller_total, num_products=seller_num_products)
                    order_id = order_rows[0][0]
                    order_ids.append(order_id)

                    # Process each item in order
                    for item in items:
                         # Add to Orders_Products
                        app.db.execute('''
                            INSERT INTO Orders_Products (order_id, product_id, seller_id, quantity, price)
                            VALUES (:order_id, :product_id, :seller_id, :quantity, :price)
                            ''', order_id=order_id, product_id=item[0], seller_id=item[1], quantity=item[2], price=item[3])

                        # Update inventory count
                        app.db.execute('''
                            UPDATE Inventory SET quantity = quantity - :order_quantity
                            WHERE product_id = :product_id AND seller_id = :seller_id
                            ''', order_quantity=item[2], product_id=item[0], seller_id=item[1])

                        # Update seller balance
                        app.db.execute('''
                            UPDATE Accounts SET current_balance = current_balance + :amount
                            WHERE user_id = :seller_id
                            ''', amount=item[2] * item[3], seller_id=item[1])

                # Update buyer balance
                app.db.execute('''
                    UPDATE Accounts SET current_balance = current_balance - :amount
                    WHERE user_id = :user_id
                    ''', amount=total_amount, user_id=user_id)

                # Clear checked-out items
                app.db.execute('''
                    DELETE FROM Cart_Products
                    WHERE cart_id = :cart_id AND status = 'in_cart' -- Delete 'in_cart' items only
                    ''', cart_id=cart_id)

                app.db.execute('COMMIT') # Finalize transaction
                logger.info(f"Checkout success user {user_id}. Orders: {order_ids}")
                return True, "Checkout successful!"

            except Exception as transaction_error:
                app.db.execute('ROLLBACK') # Revert changes on error
                logger.error(f"Transaction error checkout user {user_id}: {transaction_error}", exc_info=True)
                return False, f"Checkout error: {transaction_error}"

        except Exception as outer_error:
            # Catch errors before transaction
            logger.error(f"Checkout prep error user {user_id}: {outer_error}", exc_info=True)
            try: app.db.execute('ROLLBACK') # Attempt rollback
            except: pass
            return False, f"Unexpected error: {outer_error}"