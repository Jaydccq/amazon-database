from flask import render_template, Blueprint, jsonify, request, redirect, url_for, flash
from flask_login import current_user, login_required
from datetime import datetime

from .models.review import Review
from .models.user import User
from .models.product import Product

bp = Blueprint('reviews', __name__)

@bp.route('/api/reviews/recent/<int:user_id>', methods=['GET'])
def get_recent_reviews(user_id):
    limit = request.args.get('limit', 5, type=int)
    reviews = Review.get_recent5_by_user(user_id, limit)
    return jsonify([{
        'review_id': review.review_id,
        'user_id': review.user_id,
        'comment': review.comment,
        'review_date': review.review_date.strftime('%Y-%m-%d %H:%M:%S') if review.review_date else None,
        'product_id': review.product_id,
        'seller_id': review.seller_id,
        'rating': review.rating
    } for review in reviews])

# showing user reviews on the profile page
@bp.route('/reviews/<int:user_id>')
def user_reviews(user_id):

    user = User.get(user_id)
    if not user:
        flash('User not found!')
        return redirect(url_for('index.index'))
    
    reviews = Review.get_recent5_by_user(user_id, 5)
    
    return render_template('reviews.html', 
                          reviews=reviews,
                          user=user)

# creating a new review
@bp.route('/reviews/add', methods=['GET', 'POST'])
@login_required
def add_review():
    if request.method == 'POST':
        comment = request.form.get('comment')
        rating = int(request.form.get('rating'))
        review_type = request.form.get('review_type')
        
        if review_type == 'product':
            product_id = int(request.form.get('product_id'))
            seller_id = None
        else:
            product_id = None
            seller_id = int(request.form.get('seller_id'))
        
        
        Review.create(current_user.user_id, comment, product_id, seller_id, rating)
        flash('Review added successfully!')

        # redirect to product review or seller profile 
        if product_id:
            return redirect(url_for('products.product_detail', id=product_id))
        elif seller_id:
            return redirect(url_for('users.seller_profile', user_id=seller_id))
    
    # GET request to show the form
    product_id = request.args.get('product_id', type=int)
    seller_id = request.args.get('seller_id', type=int)
    
    product = None
    seller = None
    
    if product_id:
        product = Product.get(product_id)
    elif seller_id:
        seller = User.get(seller_id)
    
    return render_template('add_review.html',
                          product=product,
                          seller=seller)

# editing a review
@bp.route('/reviews/edit/<int:review_id>', methods=['GET', 'POST'])
@login_required
def edit_review(review_id):
    # get the review by ID
    review = Review.get(review_id)
    if not review: # if the review does not exist, redirect to the index page
        flash('Review not found!')
        return redirect(url_for('index.index'))
    
    # check if the current user is the owner of the review
    if review.user_id != current_user.user_id:
        flash('You can only edit your own reviews!')
        return redirect(url_for('index.index'))
    
    # POST request to update the review
    if request.method == 'POST':
        comment = request.form.get('comment')
        rating = int(request.form.get('rating'))
        try:
            Review.update(review_id, comment, rating)
            flash('Review updated successfully!')
        except ValueError as e:
            flash(f'Error: {str(e)}')
        # redirect to the user's reviews page
        return redirect(url_for('reviews.user_reviews', user_id=current_user.user_id))
    
    # GET request to show the edit form
    return render_template('edit_review.html', review=review)

# deleting a review
@bp.route('/api/reviews/delete/<int:review_id>', methods=['DELETE'])
@login_required
def delete_review(review_id):
    review = Review.get(review_id)
    if not review:
        return jsonify({'success': False, 
                        'error': 'Review not found'}), 404
    # check if the current user is the owner of the review
    if review.user_id != current_user.user_id:
        return jsonify({'success': False, 
                        'error': 'Unauthorized'}), 403
    
    success = Review.delete(review_id)
    return jsonify({'success': success})

# showing all reviews for a product
@bp.route('/reviews/product/<int:product_id>')
def product_reviews(product_id):
    product = Product.get(product_id)
    if not product:
        flash('Product not found!')
        return redirect(url_for('index.index'))
    
    reviews = Review.get_product_review(product_id)
    avg_rating, review_count = Review.get_avg_rating_product(product_id)
    
    return render_template('product_reviews.html',
                          product=product,
                          reviews=reviews,
                          avg_rating=avg_rating,
                          review_count=review_count)

# showing all reviews for a seller
@bp.route('/reviews/seller/<int:seller_id>')
def seller_reviews(seller_id):
    seller = User.get(seller_id)
    if not seller or not seller.is_seller:
        flash('Seller not found!')
        return redirect(url_for('index.index'))
    
    reviews = Review.get_seller_review(seller_id)
    avg_rating, review_count = Review.get_avg_rating_seller(seller_id)
    
    return render_template('seller_reviews.html',
                          seller=seller,
                          reviews=reviews,
                          avg_rating=avg_rating,
                          review_count=review_count)
