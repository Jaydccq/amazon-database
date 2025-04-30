from flask import current_app as app
from datetime import datetime

class Review:
    # Initialize review object attributes
    def __init__(self, review_id, user_id, comment, review_date, product_id, seller_id, rating, upvotes, downvotes, user_vote=None):
        self.review_id = review_id
        self.user_id = user_id
        self.comment = comment
        self.review_date = review_date
        self.product_id = product_id
        self.seller_id = seller_id
        self.rating = rating
        self.upvotes = upvotes         # Store upvotes count
        self.downvotes = downvotes     # Store downvotes count
        self.helpfulness = upvotes - downvotes # Calculate helpfulness score
        self.user_vote = user_vote     # Logged-in user's vote status

    @staticmethod
    def get(review_id, current_user_id=None): # Get one review by ID
        # Fetch review with votes
        rows = app.db.execute('''
        SELECT r.review_id, r.user_id, r.comment, r.review_date, r.product_id, r.seller_id, r.rating,
               r.upvotes, r.downvotes,
               CASE WHEN :current_user_id IS NOT NULL THEN rv.vote_type ELSE NULL END AS user_vote
        FROM Reviews_Feedbacks r
        LEFT JOIN ReviewVotes rv ON r.review_id = rv.review_id AND rv.user_id = :current_user_id
        WHERE r.review_id = :review_id
        ''',
                              review_id=review_id,
                              current_user_id=current_user_id)
        return Review(*(rows[0])) if rows else None

    @staticmethod
    def get_recent5_by_user(user_id, limit=5): # Get user's recent 5
        # Fetch recent reviews (example needs vote update)
        rows = app.db.execute('''
        SELECT r.review_id, r.user_id, r.comment, r.review_date, r.product_id, r.seller_id, r.rating,
               r.upvotes, r.downvotes,
               rv.vote_type AS user_vote
        FROM Reviews_Feedbacks r
        LEFT JOIN ReviewVotes rv ON r.review_id = rv.review_id AND rv.user_id = :user_id
        WHERE r.user_id = :user_id
        ORDER BY review_date DESC
        LIMIT :limit
        ''',
                              user_id=user_id,
                              limit=limit)
        return [Review(*row) for row in rows]


    @staticmethod
    def get_all_by_user(user_id): # Get all user reviews
        # Fetch all reviews with votes
        rows = app.db.execute('''
        SELECT r.review_id, r.user_id, r.comment, r.review_date, r.product_id, r.seller_id, r.rating,
               r.upvotes, r.downvotes,
               rv.vote_type AS user_vote
        FROM Reviews_Feedbacks r
        LEFT JOIN ReviewVotes rv ON r.review_id = rv.review_id AND rv.user_id = :user_id
        WHERE r.user_id = :user_id
        ORDER BY review_date DESC
        ''',
                              user_id=user_id)
        return [Review(*row) for row in rows]

    @staticmethod
    def get_product_review(product_id, current_user_id=None):  # Get reviews for product
        query = '''
                SELECT r.review_id, r.user_id, r.comment, r.review_date, r.product_id, r.seller_id, r.rating,
                       r.upvotes, r.downvotes,
                       CASE WHEN :current_user_id IS NOT NULL THEN rv.vote_type ELSE NULL END AS user_vote
                FROM Reviews_Feedbacks r
                LEFT JOIN ReviewVotes rv ON r.review_id = rv.review_id AND rv.user_id = :current_user_id
                WHERE r.product_id = :product_id
                ORDER BY (r.upvotes - r.downvotes) DESC, r.review_date DESC
            '''
        rows = app.db.execute(query, product_id=product_id, current_user_id=current_user_id)

        all_reviews = [Review(*row) for row in rows]

        # Sort by helpfulness score
        top_helpful = sorted(all_reviews, key=lambda x: x.helpfulness, reverse=True)
        top_3 = top_helpful[:3]
        remaining = top_helpful[3:]

        # Sort remaining by date
        remaining_sorted_by_date = sorted(remaining, key=lambda x: x.review_date, reverse=True)

        # Combine lists for final sort
        sorted_reviews = top_3 + remaining_sorted_by_date

        return sorted_reviews

    @staticmethod
    def get_seller_review(seller_id, current_user_id=None): # Get reviews for seller
        # Fetch seller reviews with votes
        query = '''
            SELECT r.review_id, r.user_id, r.comment, r.review_date, r.product_id, r.seller_id, r.rating,
                   r.upvotes, r.downvotes,
                   CASE WHEN :current_user_id IS NOT NULL THEN rv.vote_type ELSE NULL END AS user_vote
            FROM Reviews_Feedbacks r
            LEFT JOIN ReviewVotes rv ON r.review_id = rv.review_id AND rv.user_id = :current_user_id
            WHERE r.seller_id = :seller_id
            ORDER BY (r.upvotes - r.downvotes) DESC, r.review_date DESC
        '''
        rows = app.db.execute(query, seller_id=seller_id, current_user_id=current_user_id)

        # Apply same Top 3 + Recent sorting logic
        all_reviews = [Review(*row) for row in rows]
        top_helpful = sorted(all_reviews, key=lambda x: x.helpfulness, reverse=True)
        top_3 = top_helpful[:3]
        remaining = top_helpful[3:]
        remaining_sorted_by_date = sorted(remaining, key=lambda x: x.review_date, reverse=True)
        sorted_reviews = top_3 + remaining_sorted_by_date

        return sorted_reviews

    @staticmethod
    def create(user_id, comment, product_id=None, seller_id=None, rating=None): # Add a new review
        if product_id is None and seller_id is None:
            raise ValueError("Need product_id or seller_id")

        if rating is None or not (1 <= rating <= 5): # Check rating 1-5
            raise ValueError("Rating must be 1-5")

        try:
            # Insert review, initialize votes 0
            rows = app.db.execute('''
            INSERT INTO Reviews_Feedbacks(user_id, comment, product_id, seller_id, rating, review_date, upvotes, downvotes)
            VALUES(:user_id, :comment, :product_id, :seller_id, :rating, CURRENT_TIMESTAMP, 0, 0)
            RETURNING review_id
            ''',
                                  user_id=user_id,
                                  comment=comment,
                                  product_id=product_id,
                                  seller_id=seller_id,
                                  rating=rating)

            review_id = rows[0][0]
            # Return the created review object
            return Review.get(review_id, current_user_id=user_id)
        except Exception as e:
            # Handle unique constraint violation
            if 'unique constraint' in str(e).lower():
                 if product_id:
                     raise ValueError("Already reviewed this product.")
                 else:
                     raise ValueError("Already reviewed this seller.")
            print(f"Error creating review: {e}")
            raise ValueError(f"Error creating review: {e}")

    @staticmethod
    def update(review_id, comment=None, rating=None): # Update existing review comment/rating
        if comment is None and rating is None:
            return Review.get(review_id) # No changes needed

        if rating is not None and not (1 <= rating <= 5): # Check rating 1-5
            raise ValueError("Rating must be 1-5")

        update_query = []
        params = {'review_id': review_id}

        if comment is not None:
            update_query.append("comment = :comment")
            params['comment'] = comment

        if rating is not None:
            update_query.append("rating = :rating")
            params['rating'] = rating

        # Always update timestamps
        update_query.append("updated_at = CURRENT_TIMESTAMP")

        try:
            # Execute update query
            query = f'''
            UPDATE Reviews_Feedbacks
            SET {', '.join(update_query)}
            WHERE review_id = :review_id
            RETURNING review_id
            '''
            rows = app.db.execute(query, **params)

            if not rows:
                return None # Review not found
            # Return updated review object
            return Review.get(review_id) # Fetch again to get potentially needed vote info
        except Exception as e:
            print(f"Error updating review: {e}")
            raise ValueError(f"Error updating review: {e}")

    @staticmethod
    def delete(review_id): # Delete a review by ID
        try:
            # Execute delete query
            rows = app.db.execute('''
            DELETE FROM Reviews_Feedbacks
            WHERE review_id = :review_id
            RETURNING review_id
            ''',
                                  review_id=review_id)
            # Note: Associated votes deleted by CASCADE
            return rows is not None and len(rows) > 0 # Return success status
        except Exception as e:
            print(f"Error deleting review: {e}")
            return False # Return failure status

    @staticmethod
    def get_avg_rating_product(product_id): # Get product average rating
        rows = app.db.execute('''
        SELECT AVG(rating)::numeric(10,2) as avg_rating, COUNT(*) as review_count
        FROM Reviews_Feedbacks
        WHERE product_id = :product_id
        ''',
                              product_id=product_id)
        return rows[0] if rows and rows[0][0] is not None else (0.0, 0) # Handle no reviews case

    @staticmethod
    def get_avg_rating_seller(seller_id): # Get seller average rating
        rows = app.db.execute('''
        SELECT AVG(rating)::numeric(10,2) as avg_rating, COUNT(*) as review_count
        FROM Reviews_Feedbacks
        WHERE seller_id = :seller_id
        ''',
                              seller_id=seller_id)
        return rows[0] if rows and rows[0][0] is not None else (0.0, 0) # Handle no reviews case

    @staticmethod
    def add_vote(user_id, review_id, vote_type):
        """Process user vote action"""
        app.logger.debug(f"Starting vote process: user_id={user_id}, review_id={review_id}, vote_type={vote_type}")

        if vote_type not in [1, -1]:
            raise ValueError("Invalid vote type")

        # Check if vote already exists
        existing = app.db.execute('''
            SELECT vote_type FROM ReviewVotes 
            WHERE user_id = :user_id AND review_id = :review_id
        ''', user_id=user_id, review_id=review_id)

        up_delta = 0
        down_delta = 0
        new_status = None

        if existing:
            # Vote exists, check if it's the same type
            old_vote_type = existing[0][0]
            if old_vote_type == vote_type:
                # Same vote type, remove the vote
                app.db.execute('''
                    DELETE FROM ReviewVotes
                    WHERE user_id = :user_id AND review_id = :review_id
                ''', user_id=user_id, review_id=review_id)

                # Update deltas based on removed vote
                if vote_type == 1:
                    up_delta = -1
                else:
                    down_delta = -1
                new_status = None
            else:
                # Different vote type, change the vote
                app.db.execute('''
                    UPDATE ReviewVotes
                    SET vote_type = :vote_type, voted_at = CURRENT_TIMESTAMP
                    WHERE user_id = :user_id AND review_id = :review_id
                ''', vote_type=vote_type, user_id=user_id, review_id=review_id)

                # Update deltas based on changed vote
                if vote_type == 1:  # Changed to upvote
                    up_delta = 1
                    down_delta = -1
                else:  # Changed to downvote
                    up_delta = -1
                    down_delta = 1
                new_status = vote_type
        else:
            # No existing vote, add a new one
            app.db.execute('''
                INSERT INTO ReviewVotes (user_id, review_id, vote_type, voted_at)
                VALUES (:user_id, :review_id, :vote_type, CURRENT_TIMESTAMP)
            ''', user_id=user_id, review_id=review_id, vote_type=vote_type)

            # Update deltas based on new vote
            if vote_type == 1:
                up_delta = 1
            else:
                down_delta = 1
            new_status = vote_type

        # Update the review's vote counts
        try:
            updated = app.db.execute('''
                UPDATE Reviews_Feedbacks
                SET upvotes = upvotes + :up_delta,
                    downvotes = downvotes + :down_delta
                WHERE review_id = :review_id
                RETURNING upvotes, downvotes
            ''', up_delta=up_delta, down_delta=down_delta, review_id=review_id)

            if not updated:
                raise Exception("Failed updating review counts.")

            # Return the updated vote counts and vote status
            return {
                'success': True,
                'upvotes': updated[0][0],
                'downvotes': updated[0][1],
                'new_vote_status': new_status
            }
        except Exception as e:
            app.logger.error(f"Error updating vote counts: {e}", exc_info=True)
            # Re-raise the exception to be caught by the route handler
            raise