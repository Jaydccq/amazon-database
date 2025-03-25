# models/cart.py
from flask import current_app as app
from datetime import datetime

class Cart:
    @staticmethod
    def add_to_cart(user_id, product_id, seller_id, quantity):
        try:
            result = app.db.execute('''
                INSERT INTO Cart_Products (user_id, product_id, seller_id, quantity, added_at)
                VALUES (:user_id, :product_id, :seller_id, :quantity, :added_at)
                ON CONFLICT (user_id, product_id, seller_id)
                DO UPDATE SET quantity = Cart_Products.quantity + :quantity
                RETURNING user_id
            ''', user_id=user_id, product_id=product_id, seller_id=seller_id,
                 quantity=quantity, added_at=datetime.utcnow())
            return result[0][0] if result else None
        except Exception as e:
            print(f"Error adding to cart: {e}")
            return None
