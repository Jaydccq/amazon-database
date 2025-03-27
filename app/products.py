# app/products.py
from flask import Blueprint, render_template, jsonify, request, abort
from flask_login import current_user
from app.models.product import Product
from app.models.review import Review

bp = Blueprint("product", __name__, url_prefix="/products")

@bp.route("/<int:product_id>")
def product_detail(product_id):
    product = Product.get(product_id)
    if not product:
        abort(404, description="Product not found")

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