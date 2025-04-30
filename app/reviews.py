from flask import render_template, Blueprint, jsonify, request, redirect, url_for, flash
from flask_login import current_user, login_required
from datetime import datetime

# Import necessary models
from .models.review import Review
from .models.user import User
from .models.product import Product

bp = Blueprint('reviews', __name__)


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


@bp.route('/reviews/add', methods=['GET', 'POST'])
@login_required
def add_review(): # Handle adding new review
    if request.method == 'POST': # Process form submission
        comment = request.form.get('comment')
        rating = int(request.form.get('rating'))
        review_type = request.form.get('review_type') # product or seller

        product_id = None
        seller_id = None
        if review_type == 'product':
            product_id = int(request.form.get('product_id'))
        else:
            seller_id = int(request.form.get('seller_id'))

        try:
            Review.create(current_user.id, comment, product_id, seller_id, rating)
            flash('Review added successfully!')
        except ValueError as e:
            flash(f'Error: {str(e)}') # Show specific errors

        if product_id:
            return redirect(url_for('product.product_detail', product_id=product_id))
        elif seller_id:
            # Redirect to seller page if exists, otherwise profile?
            return redirect(url_for('reviews.seller_reviews', seller_id=seller_id)) # Adjusted redirect
        else:
             return redirect(url_for('reviews.user_reviews_page')) # Fallback redirect

    product_id = request.args.get('product_id', type=int)
    seller_id = request.args.get('seller_id', type=int)

    product = None
    seller = None

    if product_id:
        product = Product.get(product_id) # Get product details
    elif seller_id:
        seller = User.get(seller_id) # Get seller details

    # Render add review form
    return render_template('add_review.html',
                           product=product,
                           seller=seller)


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


@bp.route('/api/reviews/delete/<int:review_id>', methods=['DELETE'])
@login_required # Must be logged in
def delete_review(review_id): # API: Delete a review
    review = Review.get(review_id) # Get the review
    if not review:
        return jsonify({'success': False, 'error': 'Review not found'}), 404

    # Check ownership
    if review.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    # Call model delete method
    success = Review.delete(review_id)
    return jsonify({'success': success}) # Return success status


@bp.route('/reviews/vote/<int:review_id>', methods=['POST'])
@login_required # Must be logged in
def vote_review(review_id): # Process vote requests
    vote_type = request.form.get('vote_type', type=int) # Get vote type (1/-1)

    # Validate vote type
    if vote_type not in [1, -1]:
        return jsonify({'success': False, 'error': 'Invalid vote type'}), 400

    # Check if review exists
    review = Review.get(review_id)
    if not review:
        return jsonify({'success': False, 'error': 'Review not found'}), 404

    # Optional: Prevent self-voting
    # if review.user_id == current_user.id:
    #    return jsonify({'success': False, 'error': 'Cannot vote own review'}), 403

    try:
        # Call model add_vote method
        result = Review.add_vote(current_user.id, review_id, vote_type)
        return jsonify(result) # Return result from model
    except ValueError as e:
        # Return specific validation errors
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        print(f"Vote error: {e}") # Log unexpected errors
        # Return generic server error
        return jsonify({'success': False, 'error': 'Server error occurred'}), 500


@bp.route('/reviews/product/<int:product_id>')
def product_reviews(product_id): # Display product reviews page
    product = Product.get(product_id) # Get product details
    if not product:
        flash('Product not found!')
        return redirect(url_for('index.index'))

    # Get current user ID safely
    current_user_id = current_user.id if current_user.is_authenticated else None
    # Fetch reviews (sorted by model)
    reviews = Review.get_product_review(product_id, current_user_id)

    # Get average rating/count
    avg_rating, review_count = Review.get_avg_rating_product(product_id)

    # Calculate rating distribution
    rating_distribution = {star: 0 for star in range(1, 6)}
    # Fetch all just for distribution
    all_reviews_for_dist = Review.get_product_review(product_id)
    for r in all_reviews_for_dist:
         if 1 <= r.rating <= 5: # Check rating is valid
             rating_distribution[r.rating] += 1

    # Render product reviews template
    return render_template('product_reviews.html',
                           product=product,
                           reviews=reviews, # Pass sorted reviews
                           avg_rating=avg_rating,
                           review_count=review_count,
                           rating_distribution=rating_distribution)


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

    # Render seller reviews template
    return render_template('seller_reviews.html',
                           seller=seller,
                           reviews=reviews, # Pass sorted reviews
                           avg_rating=avg_rating,
                           review_count=review_count,
                           rating_distribution=rating_distribution)