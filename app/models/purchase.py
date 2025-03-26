from flask import current_app as app

class Purchase:
    def __init__(self, order_id, buyer_id, product_id, order_date):
        self.id = order_id
        self.uid = buyer_id
        self.pid = product_id
        self.time_purchased = order_date

    @staticmethod
    def get(id):
        rows = app.db.execute('''
        SELECT o.order_id, o.buyer_id, op.product_id, o.order_date
        FROM Orders o
        JOIN Orders_Products op ON o.order_id = op.order_id
        WHERE o.order_id = :id
        LIMIT 1
        ''', id=id)
        return Purchase(*(rows[0])) if rows else None

    @staticmethod
    def get_all_by_uid_since(uid, since):
        rows = app.db.execute('''
        SELECT o.order_id, o.buyer_id, op.product_id, o.order_date
        FROM Orders o
        JOIN Orders_Products op ON o.order_id = op.order_id
        WHERE o.buyer_id = :uid
        AND o.order_date >= :since
        ORDER BY o.order_date DESC
        ''', uid=uid, since=since)
        return [Purchase(*row) for row in rows]