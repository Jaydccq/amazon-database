from flask import render_template, Blueprint, jsonify, request, redirect, url_for, flash
from flask_login import current_user, login_required
from datetime import datetime

from .models.review import Review
from .models.user import User
from .models.product import Product

bp = Blueprint('reviews', __name__)


@bp.route('/user-reviews')
@login_required
def user_reviews_page():
    sort_by = request.args.get('sort_by', 'date')
    sort_order = request.args.get('sort_order', 'desc')

    rating_filter = request.args.get('rating', type=int)

    reviews = Review.get_all_by_user(current_user.id)

    # Apply filtering
    if rating_filter:
        reviews = [r for r in reviews if r.rating == rating_filter]

    if sort_by == 'rating':
        reviews = sorted(reviews, key=lambda r: r.rating,
                         reverse=(sort_order == 'desc'))
    else:
        reviews = sorted(reviews, key=lambda r: r.review_date,
                         reverse=(sort_order == 'desc'))


    return render_template('reviews.html',
                           reviews=reviews,
                           current_sort=sort_by,
                           current_order=sort_order,
                           current_rating=rating_filter)


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


@bp.route('/reviews/<int:user_id>')
def user_reviews(user_id):
    user = User.get(user_id)
    if not user:
        flash('User not found!')
        return redirect(url_for('index.index'))

    reviews = Review.get_recent5_by_user(user_id, 5)

    return render_template('user_public_reviews.html',
                           reviews=reviews,
                           user=user)


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

        try:
            Review.create(current_user.id, comment, product_id, seller_id, rating)
            flash('Review added successfully!')
        except ValueError as e:
            flash(f'Error: {str(e)}')

        if product_id:
            return redirect(url_for('product.product_detail', product_id=product_id))
        elif seller_id:
            return redirect(url_for('user_reviews', user_id=seller_id))

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


@bp.route('/reviews/edit/<int:review_id>', methods=['GET', 'POST'])
@login_required
def edit_review(review_id):
    review = Review.get(review_id)
    if not review:
        flash('Review not found!')
        return redirect(url_for('reviews.user_reviews_page'))

    if review.user_id != current_user.id:
        flash('You can only edit your own reviews!')
        return redirect(url_for('reviews.user_reviews_page'))

    if request.method == 'POST':
        comment = request.form.get('comment')
        rating = int(request.form.get('rating'))
        try:
            Review.update(review_id, comment, rating)
            flash('Review updated successfully!')
        except ValueError as e:
            flash(f'Error: {str(e)}')

        return redirect(url_for('reviews.user_reviews_page'))

    return render_template('edit_review.html', review=review)


@bp.route('/api/reviews/delete/<int:review_id>', methods=['DELETE'])
@login_required
def delete_review(review_id):
    review = Review.get(review_id)
    if not review:
        return jsonify({'success': False,
                        'error': 'Review not found'}), 404

    if review.user_id != current_user.id:
        return jsonify({'success': False,
                        'error': 'Unauthorized'}), 403

    success = Review.delete(review_id)
    return jsonify({'success': success})


@bp.route('/reviews/product/<int:product_id>')
def product_reviews(product_id):
    product = Product.get(product_id)
    if not product:
        flash('Product not found!')
        return redirect(url_for('index.index'))

    sort_by = request.args.get('sort_by', 'date')
    sort_order = request.args.get('sort_order', 'desc')

    reviews = Review.get_product_review(product_id)

    if sort_by == 'rating':
        reviews = sorted(reviews, key=lambda r: r.rating,
                         reverse=(sort_order == 'desc'))
    else:
        reviews = sorted(reviews, key=lambda r: r.review_date,
                         reverse=(sort_order == 'desc'))

    avg_rating, review_count = Review.get_avg_rating_product(product_id)

    rating_distribution = {star: 0 for star in range(1, 6)}
    for r in reviews:
        if r.rating in rating_distribution:
            rating_distribution[r.rating] += 1

    return render_template('product_reviews.html',
                           product=product,
                           reviews=reviews,
                           avg_rating=avg_rating,
                           review_count=review_count,
                           rating_distribution=rating_distribution,
                           current_sort=sort_by,
                           current_order=sort_order)


@bp.route('/reviews/seller/<int:seller_id>')
def seller_reviews(seller_id):
    seller = User.get(seller_id)
    if not seller or not seller.is_seller:
        flash('Seller not found!')
        return redirect(url_for('index.index'))
    sort_by = request.args.get('sort_by', 'date')
    sort_order = request.args.get('sort_order', 'desc')

    reviews = Review.get_seller_review(seller_id)

    if sort_by == 'rating':
        reviews = sorted(reviews, key=lambda r: r.rating,
                         reverse=(sort_order == 'desc'))
    else:  # date
        reviews = sorted(reviews, key=lambda r: r.review_date,
                         reverse=(sort_order == 'desc'))

    avg_rating, review_count = Review.get_avg_rating_seller(seller_id)
    rating_distribution = {star: 0 for star in range(1, 6)}
    for r in reviews:
        if r.rating in rating_distribution:
            rating_distribution[r.rating] += 1

    return render_template('seller_reviews.html',
                           seller=seller,
                           reviews=reviews,
                           avg_rating=avg_rating,
                           review_count=review_count,
                           rating_distribution=rating_distribution,
                           current_sort=sort_by,
                           current_order=sort_order)