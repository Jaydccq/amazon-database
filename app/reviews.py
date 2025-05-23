from flask import render_template, Blueprint, jsonify, request, redirect, url_for, flash
from flask_login import current_user, login_required
from datetime import datetime
from sqlalchemy import text
# Import necessary models
from .models.review import Review
from .models.user import User
from .models.orders import Order
from .models.product import Product
# Import the app instance
bp = Blueprint('reviews', __name__)

from flask import current_app as app
@bp.route('/user-reviews')
@login_required
def user_reviews_page(): # Display user's own reviews
    sort_by = request.args.get('sort_by', 'date') # Sort: date or rating
    sort_order = request.args.get('sort_order', 'desc') # Order: asc or desc
    rating_filter = request.args.get('rating', type=int) # Filter by rating
    recent = request.args.get('recent', type=int) # Show only recent 5?

    if recent == 1:
        reviews = Review.get_recent5_by_user(current_user.id) # Get recent 5
    else:
        reviews = Review.get_all_by_user(current_user.id) # Get all reviews

    if rating_filter:
        reviews = [r for r in reviews if r.rating == rating_filter] # Filter list

    if sort_by == 'rating':
        reviews = sorted(reviews, key=lambda r: r.rating, reverse=(sort_order == 'desc')) # Sort by rating
    else:
        reviews = sorted(reviews, key=lambda r: r.review_date, reverse=(sort_order == 'desc')) # Sort by date (default)

    # --- Render template ---
    return render_template('reviews.html',
                       reviews=reviews,
                       current_sort=sort_by,
                       current_order=sort_order,
                       current_rating=rating_filter,
                       show_recent=(recent == 1))


@bp.route('/api/reviews/recent/<int:user_id>', methods=['GET'])
def get_recent_reviews(user_id): # API: get recent reviews
    limit = request.args.get('limit', 5, type=int) # Get limit param
    reviews = Review.get_recent5_by_user(user_id, limit) # Fetch from model
    # Return JSON response
    return jsonify([{
        'review_id': review.review_id,
        'user_id': review.user_id,
        'comment': review.comment,
        'review_date': review.review_date.strftime('%Y-%m-%d %H:%M:%S') if review.review_date else None,
        'product_id': review.product_id,
        'seller_id': review.seller_id,
        'rating': review.rating,
        'upvotes': review.upvotes, # Include vote counts
        'downvotes': review.downvotes
    } for review in reviews])


@bp.route('/reviews/<int:user_id>')
def user_reviews(user_id): # Display public reviews page
    user = User.get(user_id) # Get user being viewed
    if not user:
        flash('User not found!')
        return redirect(url_for('index.index'))

    reviews = Review.get_recent5_by_user(user_id, 5) # Get their recent reviews

    # Render public reviews template
    return render_template('user_public_reviews.html',
                           reviews=reviews,
                           user=user)


# @bp.route('/reviews/add', methods=['GET', 'POST'])
# @login_required
# def add_review(): # Handle adding new review
#     if request.method == 'POST': # Process form submission
#         comment = request.form.get('comment')
#         rating = int(request.form.get('rating'))
#         review_type = request.form.get('review_type') # product or seller
#
#         product_id = None
#         seller_id = None
#         if review_type == 'product':
#             product_id = int(request.form.get('product_id'))
#         else:
#             seller_id = int(request.form.get('seller_id'))
#
#         try:
#             Review.create(current_user.id, comment, product_id, seller_id, rating)
#             flash('Review added successfully!')
#         except ValueError as e:
#             flash(f'Error: {str(e)}') # Show specific errors
#
#         if product_id:
#             return redirect(url_for('product.product_detail', product_id=product_id))
#         elif seller_id:
#             # Redirect to seller page if exists, otherwise profile?
#             return redirect(url_for('reviews.seller_reviews', seller_id=seller_id)) # Adjusted redirect
#         else:
#              return redirect(url_for('reviews.user_reviews_page')) # Fallback redirect
#
#     product_id = request.args.get('product_id', type=int)
#     seller_id = request.args.get('seller_id', type=int)
#
#     product = None
#     seller = None
#
#     if product_id:
#         product = Product.get(product_id) # Get product details
#     elif seller_id:
#         seller = User.get(seller_id) # Get seller details
#
#     # Render add review form
#     return render_template('add_review.html',
#                            product=product,
#                            seller=seller)


@bp.route('/reviews/edit/<int:review_id>', methods=['GET', 'POST'])
@login_required # Must be logged in
def edit_review(review_id): # Handle editing own review
    # Get review, pass user ID
    review = Review.get(review_id, current_user.id)
    if not review:
        flash('Review not found!')
        return redirect(url_for('reviews.user_reviews_page'))

    # Check ownership
    if review.user_id != current_user.id:
        flash('Cannot edit others reviews!')
        return redirect(url_for('reviews.user_reviews_page'))

    if request.method == 'POST': # Process form submission
        comment = request.form.get('comment')
        rating = int(request.form.get('rating'))
        try:
            # Call model update method
            Review.update(review_id, comment, rating)
            flash('Review updated successfully!')
        except ValueError as e:
            flash(f'Error: {str(e)}')

        return redirect(url_for('reviews.user_reviews_page')) # Redirect to user reviews

    # Render edit review form
    return render_template('edit_review.html', review=review)


@bp.route('/reviews/product/<int:product_id>')
def product_reviews(product_id):
    page = request.args.get('page', 1, type=int)
    per_page = 10  # 10 reviews per page

    product = Product.get(product_id)
    if not product:
        flash('Product not found!')
        return redirect(url_for('index.index'))

    # Get current user ID safely
    current_user_id = current_user.id if current_user.is_authenticated else None

    # Get total number of reviews for this product
    all_reviews = Review.get_product_review(product_id, current_user_id)

    # Calculate total pages
    total_reviews = len(all_reviews)
    total_pages = (total_reviews + per_page - 1) // per_page

    # Get only reviews for current page
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_reviews = all_reviews[start_idx:end_idx]

    # Get average rating/count
    avg_rating, review_count = Review.get_avg_rating_product(product_id)

    # Calculate rating distribution
    rating_distribution = {star: 0 for star in range(1, 6)}
    for r in all_reviews:
        if 1 <= r.rating <= 5:
            rating_distribution[r.rating] += 1

    return render_template('product_reviews.html',
                           product=product,
                           reviews=paginated_reviews,
                           avg_rating=avg_rating,
                           review_count=review_count,
                           rating_distribution=rating_distribution,
                           page=page,
                           total_pages=total_pages,
                           per_page=per_page)


@bp.route('/reviews/seller/<int:seller_id>')
def seller_reviews(seller_id): # Display seller reviews page
    seller = User.get(seller_id) # Get seller details
    if not seller or not seller.is_seller:
        flash('Seller not found!')
        return redirect(url_for('index.index'))

    # Get current user ID safely
    current_user_id = current_user.id if current_user.is_authenticated else None
    # Fetch seller reviews (sorted)
    reviews = Review.get_seller_review(seller_id, current_user_id)

    # Get average rating/count
    avg_rating, review_count = Review.get_avg_rating_seller(seller_id)

    # Calculate rating distribution
    rating_distribution = {star: 0 for star in range(1, 6)}
    all_reviews_for_dist = Review.get_seller_review(seller_id) # Fetch all for distribution
    for r in all_reviews_for_dist:
        if 1 <= r.rating <= 5:
            rating_distribution[r.rating] += 1

    return render_template('seller_reviews.html',
                           seller=seller,
                           reviews=reviews, # Pass sorted reviews
                           avg_rating=avg_rating,
                           review_count=review_count,
                           rating_distribution=rating_distribution,
                           Order=Order)


@bp.route('/reviews/vote/<int:review_id>', methods=['POST'])
@login_required
def vote_review(review_id):
    # Get the vote type from the form (1 for upvote, -1 for downvote)
    vote_type = request.form.get('vote_type', type=int)

    # Validate the vote type
    if vote_type not in [1, -1]:
        flash('Invalid vote type', 'danger')
        return redirect(request.referrer or url_for('index.index'))

    # Check if the review exists
    review = Review.get(review_id)
    if not review:
        flash('Review does not exist', 'danger')
        return redirect(request.referrer or url_for('index.index'))

    # Prevent users from voting on their own reviews
    if review.user_id == current_user.id:
        flash('You cannot vote on your own review', 'danger')
        return redirect(request.referrer or url_for('index.index'))

    try:
        # Handle the voting logic
        result = Review.add_vote(current_user.id, review_id, vote_type)
        if result.get('success'):
            flash('Vote submitted successfully!', 'success')
        else:
            flash(f'Voting error: {result.get("error", "Unknown error")}', 'danger')
    except Exception as e:
        flash(f'Server error: {str(e)}', 'danger')

    # Redirect back to the previous page
    return redirect(request.referrer or url_for('index.index'))


@bp.route('/reviews/delete/<int:review_id>', methods=['POST'])
@login_required
def delete_review(review_id):
    # Retrieve the review
    review = Review.get(review_id)

    # Check if the review exists
    if not review:
        flash('Review does not exist', 'danger')
        return redirect(request.referrer or url_for('index.index'))

    # Ensure that only the author can delete their own review
    if review.user_id != current_user.id:
        flash('You do not have permission to delete this review', 'danger')
        return redirect(request.referrer or url_for('index.index'))

    # Delete the review
    success = Review.delete(review_id)

    if success:
        flash('Review deleted successfully', 'success')
    else:
        flash('Failed to delete the review', 'danger')

    # Redirect to the appropriate page depending on context
    if review.product_id:
        return redirect(url_for('product.product_detail', product_id=review.product_id))
    elif review.seller_id:
        return redirect(url_for('reviews.seller_reviews', seller_id=review.seller_id))
    else:
        return redirect(url_for('reviews.user_reviews_page'))


@bp.route('/reviews/add', methods=['GET', 'POST'])
@login_required
def add_review():
    if request.method == 'POST':
        comment = request.form.get('comment')
        rating = int(request.form.get('rating'))
        review_type = request.form.get('review_type')  # product or seller

        product_id = None
        seller_id = None
        if review_type == 'product':
            product_id = int(request.form.get('product_id'))
        else:
            seller_id = int(request.form.get('seller_id'))

            # Check if user has purchased from this seller
            has_purchased = Order.has_user_purchased_from_seller(current_user.id, seller_id)
            if not has_purchased:
                flash('You can only review sellers you have purchased from.', 'error')
                return redirect(url_for('reviews.seller_reviews', seller_id=seller_id))

        try:
            Review.create(current_user.id, comment, product_id, seller_id, rating)
            flash('Review added successfully!')
        except ValueError as e:
            flash(f'Error: {str(e)}')

        if product_id:
            return redirect(url_for('product.product_detail', product_id=product_id))
        elif seller_id:
            return redirect(url_for('reviews.seller_reviews', seller_id=seller_id))
        else:
            return redirect(url_for('reviews.user_reviews_page'))

    product_id = request.args.get('product_id', type=int)
    seller_id = request.args.get('seller_id', type=int)

    product = None
    seller = None

    if product_id:
        product = Product.get(product_id)
    elif seller_id:
        seller = User.get(seller_id)

        # Check if user has purchased from this seller
        has_purchased = Order.has_user_purchased_from_seller(current_user.id, seller_id)
        if not has_purchased:
            flash('You can only review sellers you have purchased from.', 'error')
            return redirect(url_for('reviews.seller_reviews', seller_id=seller_id))

    return render_template('add_review.html',
                           product=product,
                           seller=seller)


@bp.route('/api/seller/<int:seller_id>/reviews')
def api_seller_reviews(seller_id):
    """API endpoint to get seller reviews data for AJAX"""
    # Get seller reviews
    reviews = Review.get_seller_review(seller_id)

    # Get average rating and review count
    avg_rating, review_count = Review.get_avg_rating_seller(seller_id)

    # Get top review (highest helpfulness score)
    top_review = None
    if reviews:
        top_review = max(reviews, key=lambda r: r.helpfulness)
        top_review = {
            'review_id': top_review.review_id,
            'user_id': top_review.user_id,
            'comment': top_review.comment,
            'review_date': top_review.review_date.strftime('%Y-%m-%d'),
            'rating': top_review.rating,
            'helpfulness': top_review.helpfulness
        }

    # Return JSON response
    return jsonify({
        'seller_id': seller_id,
        'avg_rating': float(avg_rating) if avg_rating else None,
        'count': review_count,
        'top_review': top_review
    })
