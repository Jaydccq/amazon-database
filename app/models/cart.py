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

    @staticmethod
    def checkout_cart(user_id):
        try:
            # 获取用户购物车ID
            cart_rows = app.db.execute('''
                    SELECT cart_id FROM Carts WHERE user_id = :user_id
                ''', user_id=user_id)

            if not cart_rows:
                return False, "cart does not exist"

            cart_id = cart_rows[0][0]

            # 获取购物车中的商品，并验证库存
            cart_items = app.db.execute('''
                SELECT 
                    cp.product_id, 
                    cp.seller_id, 
                    cp.quantity, 
                    i.unit_price,
                    i.quantity as available_quantity
                FROM Cart_Products cp
                JOIN Inventory i ON cp.product_id = i.product_id AND cp.seller_id = i.seller_id
                WHERE cp.cart_id = :cart_id
                ''', cart_id=cart_id)

            if not cart_items:
                return False, "购物车为空"

            # 检查库存是否充足
            insufficient_items = []
            for item in cart_items:
                if item[2] > item[4]:
                    product_name = app.db.execute('''
                        SELECT product_name FROM Products WHERE product_id = :product_id
                        ''', product_id=item[0])[0][0]
                    insufficient_items.append(f"{product_name} (需要: {item[2]}, 库存: {item[4]})")

            if insufficient_items:
                return False, f"以下商品库存不足: {', '.join(insufficient_items)}"

            # 计算总金额
            total_amount = sum(item[2] * item[3] for item in cart_items)

            # 检查用户余额是否充足
            user_balance = app.db.execute('''
                SELECT current_balance FROM Accounts WHERE user_id = :user_id
                ''', user_id=user_id)[0][0]

            if user_balance < total_amount:
                return False, f"余额不足。需要: ${total_amount:.2f}, 当前余额: ${user_balance:.2f}"

            # 开始事务，确保所有操作要么全部成功，要么全部失败
            app.db.execute('BEGIN')

            # 按照卖家分组购物车商品
            sellers_items = {}
            for item in cart_items:
                seller_id = item[1]
                if seller_id not in sellers_items:
                    sellers_items[seller_id] = []
                sellers_items[seller_id].append(item)

            # 为每个卖家创建一个订单
            order_ids = []
            for seller_id, items in sellers_items.items():
                seller_total = sum(item[2] * item[3] for item in items)
                seller_num_products = sum(item[2] for item in items)

                # 创建订单
                order_rows = app.db.execute('''
                    INSERT INTO Orders (buyer_id, total_amount, num_products, order_date)
                    VALUES (:user_id, :total_amount, :num_products, CURRENT_TIMESTAMP)
                    RETURNING order_id
                    ''', user_id=user_id, total_amount=seller_total, num_products=seller_num_products)

                order_id = order_rows[0][0]
                order_ids.append(order_id)

                # 添加订单商品
                for item in items:
                    app.db.execute('''
                        INSERT INTO Orders_Products (order_id, product_id, seller_id, quantity, price)
                        VALUES (:order_id, :product_id, :seller_id, :quantity, :price)
                        ''', order_id=order_id,
                                   product_id=item[0],
                                   seller_id=item[1],
                                   quantity=item[2],
                                   price=item[3])

                    # 更新库存
                    app.db.execute('''
                        UPDATE Inventory
                        SET quantity = quantity - :order_quantity
                        WHERE product_id = :product_id AND seller_id = :seller_id
                        ''', order_quantity=item[2], product_id=item[0], seller_id=item[1])

                    # 增加卖家余额
                    app.db.execute('''
                        UPDATE Accounts
                        SET current_balance = current_balance + :amount
                        WHERE user_id = :seller_id
                        ''', amount=item[2] * item[3], seller_id=item[1])

            # 扣减买家余额
            app.db.execute('''
                UPDATE Accounts
                SET current_balance = current_balance - :amount
                WHERE user_id = :user_id
                ''', amount=total_amount, user_id=user_id)

            # 清空购物车
            app.db.execute('''
                DELETE FROM Cart_Products
                WHERE cart_id = :cart_id
                ''', cart_id=cart_id)

            # 提交事务
            app.db.execute('COMMIT')

            return True, order_ids

        except Exception as e:
            # 回滚事务
            app.db.execute('ROLLBACK')
            import traceback
            print("======== CHECKOUT ERROR ========")
            traceback.print_exc()
            return False, str(e)

