from flask import current_app as app
from datetime import datetime


class Cart:
    @staticmethod
    def add_to_cart(user_id, product_id, seller_id, quantity):
        try:
            cart_rows = app.db.execute('''
            SELECT cart_id FROM Carts 
            WHERE user_id = :user_id
            ''', user_id=user_id)

            if not cart_rows:
                app.db.execute('''
                INSERT INTO Carts (user_id, created_at, updated_at)
                VALUES (:user_id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ''', user_id=user_id)

                cart_rows = app.db.execute('''
                SELECT cart_id FROM Carts 
                WHERE user_id = :user_id
                ''', user_id=user_id)

            cart_id = cart_rows[0][0]

            # Get the current price from inventory
            price_rows = app.db.execute('''
            SELECT unit_price FROM Inventory
            WHERE product_id = :product_id AND seller_id = :seller_id
            ''', product_id=product_id, seller_id=seller_id)

            if not price_rows:
                return None

            unit_price = price_rows[0][0]

            # Add to cart or update quantity
            result = app.db.execute('''
            INSERT INTO Cart_Products (cart_id, product_id, seller_id, quantity, price_at_addition, added_at)
            VALUES (:cart_id, :product_id, :seller_id, :quantity, :price, :added_at)
            ON CONFLICT (cart_id, product_id, seller_id)
            DO UPDATE SET quantity = Cart_Products.quantity + :quantity,
                          price_at_addition = :price,
                          added_at = :added_at
            RETURNING cart_id
            ''', cart_id=cart_id, product_id=product_id,
                                    seller_id=seller_id, quantity=quantity,
                                    price=unit_price, added_at=datetime.utcnow())

            return result[0][0] if result else None
        except Exception as e:
            print(f"Error adding to cart: {e}")
            return None

    @staticmethod
    def get_cart_items(user_id):
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
                CONCAT(a.first_name, ' ', a.last_name) as seller_name
            FROM Cart_Products cp
            JOIN Carts c ON cp.cart_id = c.cart_id
            JOIN Products p ON cp.product_id = p.product_id
            JOIN Accounts a ON cp.seller_id = a.user_id
            WHERE c.user_id = :user_id
            ''', user_id=user_id)
            return result
        except Exception as e:
            print(f"Error retrieving cart items: {e}")
            return []