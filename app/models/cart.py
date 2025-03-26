# models/cart.py
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

            result = app.db.execute('''
            INSERT INTO Cart_Products (cart_id, product_id, seller_id, quantity, added_at)
            VALUES (:cart_id, :product_id, :seller_id, :quantity, :added_at)
            ON CONFLICT (cart_id, product_id, seller_id)
            DO UPDATE SET quantity = Cart_Products.quantity + :quantity
            RETURNING cart_id
            ''', cart_id=cart_id, product_id=product_id,
                                    seller_id=seller_id, quantity=quantity,
                                    added_at=datetime.utcnow())

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
                i.unit_price,
                (cp.quantity * i.unit_price) as total_price
            FROM Cart_Products cp
            JOIN Carts c ON cp.cart_id = c.cart_id
            JOIN Products p ON cp.product_id = p.product_id
            JOIN Inventory i ON cp.product_id = i.product_id AND cp.seller_id = i.seller_id
            WHERE c.user_id = :user_id
            ''', user_id=user_id)
            return result
        except Exception as e:
            print(f"Error retrieving cart items: {e}")
            return []