from flask import current_app as app
from datetime import datetime


class OrderItem:
    def __init__(self, order_item_id, order_id, product_id, quantity, price,
                 seller_id, status, fulfillment_date, product_name=None,
                 seller_name=None, image=None):
        self.order_item_id = order_item_id
        self.order_id = order_id
        self.product_id = product_id
        self.quantity = quantity
        self.price = price
        self.seller_id = seller_id
        self.status = status
        self.fulfillment_date = fulfillment_date
        self.product_name = product_name
        self.seller_name = seller_name
        self.image = image

    def get_subtotal(self):
        """Calculate subtotal for this item"""
        return float(self.price) * self.quantity

    @staticmethod
    def get(order_item_id):
        """Get order item by ID"""
        rows = app.db.execute('''
            SELECT op.order_item_id, op.order_id, op.product_id, op.quantity, 
                   op.price, op.seller_id, op.status, op.fulfillment_date,
                   p.product_name, CONCAT(a.first_name, ' ', a.last_name) AS seller_name, p.image
            FROM Orders_Products op
            JOIN Products p ON op.product_id = p.product_id
            JOIN Accounts a ON op.seller_id = a.user_id
            WHERE op.order_item_id = :order_item_id
        ''', order_item_id=order_item_id)

        return OrderItem(*(rows[0])) if rows else None

    @staticmethod
    def get_for_order(order_id):
        """Get all items for an order"""
        rows = app.db.execute('''
            SELECT op.order_item_id, op.order_id, op.product_id, op.quantity, 
                   op.price, op.seller_id, op.status, op.fulfillment_date,
                   p.product_name, CONCAT(a.first_name, ' ', a.last_name) AS seller_name, p.image
            FROM Orders_Products op
            JOIN Products p ON op.product_id = p.product_id
            JOIN Accounts a ON op.seller_id = a.user_id
            WHERE op.order_id = :order_id
            ORDER BY a.first_name,a.last_name, p.product_name
        ''', order_id=order_id)

        return [OrderItem(*row) for row in rows]

    @staticmethod
    def get_for_order_and_seller(order_id, seller_id):
        """Get items for an order that belong to a specific seller"""
        rows = app.db.execute('''
            SELECT op.order_item_id, op.order_id, op.product_id, op.quantity, 
                   op.price, op.seller_id, op.status, op.fulfillment_date,
                   p.product_name, CONCAT(a.first_name, ' ', a.last_name) AS seller_name, p.image
            FROM Orders_Products op
            JOIN Products p ON op.product_id = p.product_id
            JOIN Accounts a ON op.seller_id = a.user_id
            WHERE op.order_id = :order_id AND op.seller_id = :seller_id
            ORDER BY p.product_name
        ''', order_id=order_id, seller_id=seller_id)

        return [OrderItem(*row) for row in rows]

    @staticmethod
    def fulfill(order_item_id, seller_id):
        """Mark an order item as fulfilled"""
        try:
            # Verify the item belongs to this seller and is not already fulfilled
            result = app.db.execute('''
                UPDATE Orders_Products 
                SET status = 'Fulfilled', fulfillment_date = :now
                WHERE order_item_id = :order_item_id 
                AND seller_id = :seller_id 
                AND status = 'Unfulfilled'
                RETURNING order_id
            ''', order_item_id=order_item_id, seller_id=seller_id, now=datetime.utcnow())

            if not result:
                return False, "Item not found or already fulfilled"

            order_id = result[0][0]

            # Check if all items in the order are fulfilled
            unfulfilled = app.db.execute('''
                SELECT COUNT(*) 
                FROM Orders_Products 
                WHERE order_id = :order_id AND status = 'Unfulfilled'
            ''', order_id=order_id)

            # If no unfulfilled items remain, update order status
            if unfulfilled[0][0] == 0:
                app.db.execute('''
                    UPDATE Orders 
                    SET order_status = 'Fulfilled'
                    WHERE order_id = :order_id
                ''', order_id=order_id)

            return True, None

        except Exception as e:
            print(f"Error fulfilling order item: {e}")
            return False, str(e)


class Order:
    def __init__(self, order_id, buyer_id, total_amount, order_date,
                 num_products, order_status, buyer_name=None, address=None):
        self.order_id = order_id
        self.buyer_id = buyer_id
        self.total_amount = total_amount
        self.order_date = order_date
        self.num_products = num_products
        self.order_status = order_status
        self.buyer_name = buyer_name
        self.address = address
        self.items = []  # Will be populated separately

    @staticmethod
    def get(order_id):
        """Get order details by ID"""
        rows = app.db.execute('''
            SELECT o.order_id, o.buyer_id, o.total_amount, o.order_date, 
                   o.num_products, o.order_status, CONCAT(a.first_name, ' ', a.last_name) AS buyer_name, 
                   a.address
            FROM Orders o
            JOIN Accounts a ON o.buyer_id = a.user_id
            WHERE o.order_id = :order_id
        ''', order_id=order_id)

        if not rows:
            return None

        order = Order(*(rows[0]))
        order.items = OrderItem.get_for_order(order_id)

        return order

    @staticmethod
    def get_for_buyer(buyer_id, limit=10, offset=0, status=None):
        """Get orders for a specific buyer"""
        query = '''
            SELECT o.order_id, o.buyer_id, o.total_amount, o.order_date, 
                   o.num_products, o.order_status, CONCAT(a.first_name, ' ', a.last_name) AS buyer_name, 
                   a.address
            FROM Orders o
            JOIN Accounts a ON o.buyer_id = a.user_id
            WHERE o.buyer_id = :buyer_id
        '''
        params = {'buyer_id': buyer_id}

        if status:
            query += " AND o.order_status = :status"
            params['status'] = status

        query += " ORDER BY o.order_date DESC LIMIT :limit OFFSET :offset"
        params['limit'] = limit
        params['offset'] = offset

        rows = app.db.execute(query, **params)

        orders = []
        for row in rows:
            order = Order(*row)
            order.items = OrderItem.get_for_order(order.order_id)
            orders.append(order)

        return orders

    @staticmethod
    def count_for_buyer(buyer_id, status=None):
        """Count buyer orders for pagination"""
        query = "SELECT COUNT(*) FROM Orders WHERE buyer_id = :buyer_id"
        params = {'buyer_id': buyer_id}

        if status:
            query += " AND order_status = :status"
            params['status'] = status

        result = app.db.execute(query, **params)
        return result[0][0] if result else 0

    @staticmethod
    def get_for_seller(seller_id, limit=10, offset=0, status=None):
        """Get orders containing items sold by a specific seller"""
        query = '''
            SELECT DISTINCT o.order_id, o.buyer_id, o.total_amount, o.order_date, 
                   o.num_products, o.order_status, CONCAT(a.first_name, ' ', a.last_name) AS buyer_name, 
                   a.address
            FROM Orders o
            JOIN Orders_Products op ON o.order_id = op.order_id
            JOIN Accounts a ON o.buyer_id = a.user_id
            WHERE op.seller_id = :seller_id
        '''
        params = {'seller_id': seller_id}

        if status:
            if status == 'Fulfilled':
                query += '''
                    AND NOT EXISTS (
                        SELECT 1 FROM Orders_Products 
                        WHERE order_id = o.order_id 
                        AND seller_id = :seller_id_check 
                        AND status = 'Unfulfilled'
                    )
                '''
                params['seller_id_check'] = seller_id
            elif status == 'Unfulfilled':
                query += '''
                    AND EXISTS (
                        SELECT 1 FROM Orders_Products 
                        WHERE order_id = o.order_id 
                        AND seller_id = :seller_id_check 
                        AND status = 'Unfulfilled'
                    )
                '''
                params['seller_id_check'] = seller_id

        query += " ORDER BY o.order_date DESC LIMIT :limit OFFSET :offset"
        params['limit'] = limit
        params['offset'] = offset

        rows = app.db.execute(query, **params)

        orders = []
        for row in rows:
            order = Order(*row)
            # Only include items for this seller
            order.items = OrderItem.get_for_order_and_seller(order.order_id, seller_id)
            orders.append(order)

        return orders

    @staticmethod
    def count_for_seller(seller_id, status=None):
        """Count seller orders for pagination"""
        query = '''
            SELECT COUNT(DISTINCT o.order_id)
            FROM Orders o
            JOIN Orders_Products op ON o.order_id = op.order_id
            WHERE op.seller_id = :seller_id
        '''
        params = {'seller_id': seller_id}

        if status:
            if status == 'Fulfilled':
                query += '''
                    AND NOT EXISTS (
                        SELECT 1 FROM Orders_Products 
                        WHERE order_id = o.order_id 
                        AND seller_id = :seller_id_check 
                        AND status = 'Unfulfilled'
                    )
                '''
                params['seller_id_check'] = seller_id
            elif status == 'Unfulfilled':
                query += '''
                    AND EXISTS (
                        SELECT 1 FROM Orders_Products 
                        WHERE order_id = o.order_id 
                        AND seller_id = :seller_id_check 
                        AND status = 'Unfulfilled'
                    )
                '''
                params['seller_id_check'] = seller_id

        result = app.db.execute(query, **params)
        return result[0][0] if result else 0

    @staticmethod
    def get_filtered_orders(buyer_id, search_query=None, seller_id=None, product_id=None,
                            from_date=None, to_date=None, status=None,
                            sort_by='date', sort_order='desc', limit=100, offset=0):
        """Get filtered orders for a buyer"""

        # Start building the query
        query = '''
            SELECT DISTINCT o.order_id, o.buyer_id, o.total_amount, o.order_date, 
                   o.num_products, o.order_status, CONCAT(a.first_name, ' ', a.last_name) AS buyer_name, 
                   a.address
            FROM Orders o
            JOIN Accounts a ON o.buyer_id = a.user_id
        '''

        # Add necessary joins based on filters
        if search_query or product_id or seller_id:
            query += ' JOIN Orders_Products op ON o.order_id = op.order_id'

        if search_query or product_id:
            query += ' JOIN Products p ON op.product_id = p.product_id'

        if search_query or seller_id:
            query += ' JOIN Accounts s ON op.seller_id = s.user_id'

        # Where clause
        query += ' WHERE o.buyer_id = :buyer_id'

        # Initialize parameters dictionary
        params = {'buyer_id': buyer_id}

        # Add filter conditions
        if search_query:
            query += ''' AND (
                p.product_name ILIKE :search_query OR
                CONCAT(s.first_name, ' ', s.last_name) ILIKE :search_query
            )'''
            params['search_query'] = f'%{search_query}%'

        if seller_id:
            query += ' AND op.seller_id = :seller_id'
            params['seller_id'] = seller_id

        if product_id:
            query += ' AND op.product_id = :product_id'
            params['product_id'] = product_id

        if from_date:
            query += ' AND o.order_date >= :from_date'
            params['from_date'] = from_date

        if to_date:
            query += ' AND o.order_date <= :to_date'
            params['to_date'] = to_date

        if status:
            query += ' AND o.order_status = :status'
            params['status'] = status

        # Add sorting
        if sort_by == 'price':
            query += ' ORDER BY o.total_amount'
        elif sort_by == 'status':
            query += ' ORDER BY o.order_status'
        else:  # default to date
            query += ' ORDER BY o.order_date'

        # Add sort direction
        query += ' DESC' if sort_order == 'desc' else ' ASC'

        # Add pagination
        query += ' LIMIT :limit OFFSET :offset'
        params['limit'] = limit
        params['offset'] = offset

        # Execute query
        rows = app.db.execute(query, **params)

        # Process results
        orders = []
        for row in rows:
            order = Order(*row)
            # Get items for each order
            order.items = OrderItem.get_for_order(order.order_id)
            orders.append(order)

        return orders

    @staticmethod
    def get_sellers_for_buyer(buyer_id):
        """Get list of sellers that the buyer has ordered from"""
        rows = app.db.execute('''
            SELECT DISTINCT s.user_id, CONCAT(s.first_name, ' ', s.last_name) AS seller_name
            FROM Orders o
            JOIN Orders_Products op ON o.order_id = op.order_id
            JOIN Accounts s ON op.seller_id = s.user_id
            WHERE o.buyer_id = :buyer_id
            ORDER BY seller_name
        ''', buyer_id=buyer_id)

        return [{'id': row[0], 'name': row[1]} for row in rows]

    @staticmethod
    def get_products_for_buyer(buyer_id):
        """Get list of products that the buyer has ordered"""
        rows = app.db.execute('''
            SELECT DISTINCT p.product_id, p.product_name
            FROM Orders o
            JOIN Orders_Products op ON o.order_id = op.order_id
            JOIN Products p ON op.product_id = p.product_id
            WHERE o.buyer_id = :buyer_id
            ORDER BY p.product_name
        ''', buyer_id=buyer_id)

        return [{'id': row[0], 'name': row[1]} for row in rows]