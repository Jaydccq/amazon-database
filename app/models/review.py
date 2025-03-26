#review part created by chx
from flask import current_app as app
from datetime import datetime

class Review:
    def __init__(self, review_id, user_id, comment, review_date, product_id, seller_id, rating):
        self.review_id = review_id
        self.user_id = user_id
        self.comment = comment
        self.review_date = review_date
        self.product_id = product_id
        self.seller_id = seller_id
        self.rating = rating

    @staticmethod
    def get(review_id):
        rows = app.db.execute('''
        SELECT review_id, user_id, comment, review_date, product_id, seller_id, rating
        FROM Reviews_Feedbacks
        WHERE review_id = :review_id
        ''',
        review_id=review_id)
        return Review(*(rows[0])) if rows else None

    @staticmethod
    def get_recent5_by_user(user_id, limit=5):
        rows = app.db.execute('''
        SELECT review_id, user_id, comment, review_date, product_id, seller_id, rating
        FROM Reviews_Feedbacks
        WHERE user_id = :user_id
        ORDER BY review_date DESC
        LIMIT :limit
        ''',
        user_id=user_id,
        limit=limit)
        return [Review(*row) for row in rows]

    @staticmethod
    def get_product_review(product_id):
        rows = app.db.execute('''
        SELECT review_id, user_id, comment, review_date, product_id, seller_id, rating
        FROM Reviews_Feedbacks
        WHERE product_id = :product_id
        ORDER BY review_date DESC
        ''',
        product_id=product_id)
        return [Review(*row) for row in rows]

    @staticmethod
    def get_seller_review(seller_id):
        rows = app.db.execute('''
        SELECT review_id, user_id, comment, review_date, product_id, seller_id, rating
        FROM Reviews_Feedbacks
        WHERE seller_id = :seller_id
        ORDER BY review_date DESC
        ''',
        seller_id=seller_id)
        return [Review(*row) for row in rows]

    @staticmethod
    def create(user_id, comment, product_id=None, seller_id=None, rating=None):
        if product_id is None and seller_id is None:
            raise ValueError("Either product_id or seller_id is required")
        
        if rating is None or not (0 <= rating <= 5):
            raise ValueError("Rating must be between 0 and 5")

        rows = app.db.execute('''
        INSERT INTO Reviews_Feedbacks(user_id, comment, product_id, seller_id, rating)
        VALUES(:user_id, :comment, :product_id, :seller_id, :rating)
        RETURNING review_id
        ''',
        user_id=user_id,
        comment=comment,
        product_id=product_id,
        seller_id=seller_id,
        rating=rating)

        review_id = rows[0][0]
        return Review.get(review_id)

    @staticmethod
    def update(review_id, comment=None, rating=None):
        # check if review exists
        if comment is None and rating is None:
            return Review.get(review_id)
        
        if rating is not None and not (0 <= rating <= 5):
            raise ValueError("Rating must be between 0 and 5")
        
        # update query
        update_query = []
        params = {'review_id': review_id}
        
        if comment is not None:
            update_query.append("comment = :comment")
            params['comment'] = comment
        
        if rating is not None:
            update_query.append("rating = :rating")
            params['rating'] = rating
            
        update_query.append("review_date = CURRENT_TIMESTAMP")
        
        query = f'''
        UPDATE Reviews_Feedbacks
        SET {', '.join(update_query)}
        WHERE review_id = :review_id
        RETURNING review_id
        '''
        rows = app.db.execute(query, **params)
        # check if update was successful
        if not rows:
            return None
        return Review.get(review_id)

    @staticmethod
    def delete(review_id):

        rows = app.db.execute('''
        DELETE FROM Reviews_Feedbacks
        WHERE review_id = :review_id
        RETURNING review_id
        ''',
        review_id=review_id)
        return rows is not None and len(rows) > 0

    @staticmethod
    def get_avg_rating_product(product_id):
        rows = app.db.execute('''
        SELECT AVG(rating) as avg_rating, COUNT(*) as review_count
        FROM Reviews_Feedbacks
        WHERE product_id = :product_id
        ''',
        product_id=product_id)
        return rows[0] if rows else (0, 0)

    @staticmethod
    def get_avg_rating_seller(seller_id):
        rows = app.db.execute('''
        SELECT AVG(rating) as avg_rating, COUNT(*) as review_count
        FROM Reviews_Feedbacks
        WHERE seller_id = :seller_id
        ''',
        seller_id=seller_id)
        return rows[0] if rows else (0, 0)