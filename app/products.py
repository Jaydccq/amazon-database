# app/products.py
from flask import Blueprint, render_template, jsonify, request, abort
from flask_login import current_user
from app.models.product import Product
from app.models.review import Review
from app.models.inventory import Inventory

bp = Blueprint("product", __name__, url_prefix="/products")

@bp.route("/<int:product_id>")
def product_detail(product_id):
    product = Product.get(product_id)
    if not product:
        abort(404, description="Product not found")

    inventory_items = Inventory.get_sellers_for_product(product_id)

    product.inventory = inventory_items

    reviews = Review.get_product_review(product_id)
    reviews = Review.get_product_review(product_id)


    return render_template("product_detail.html",
                           product=product,
                           reviews=reviews)


@bp.route("/api/<int:product_id>")
def product_api(product_id):
    product = Product.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    return jsonify(product.to_dict())


@bp.route("/expensive/<int:k>")
def top_expensive_products(k):
    products = Product.get_top_k_expensive(k)
    return render_template("top_expensive.html", products=products)

@bp.route("/api/expensive/<int:k>")
def api_top_expensive_products(k):
    products = Product.get_top_k_expensive(k)
    return jsonify([{
        'id': product.id,
        'name': product.name,
        'description': product.description,
        'category_id': product.category_id,
        'category_name': product.category_name,
        'price': float(product.price) if product.price else None,
        'owner_id': product.owner_id,
        'owner_name': product.owner_name,
        'avg_rating': float(product.avg_rating) if product.avg_rating else 0,
        'review_count': product.review_count
    } for product in products])