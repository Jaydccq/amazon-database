from flask import Blueprint, render_template, jsonify,request
from app.models.product import Product

bp = Blueprint("product", __name__, url_prefix="/products")

@bp.route('/products')
def product_list():
    try:
        k = int(request.args.get('k'))
    except (TypeError, ValueError):
        k = None

    try:
        category_id = int(request.args.get('category_id'))
    except (TypeError, ValueError):
        category_id = None

    products = Product.get_all_with_min_price(k=k, category_id=category_id)
    return render_template('products.html', products=products)


@bp.route("/<int:product_id>")
def product_detail(product_id):
    product = Product.get(product_id)
    if not product:
        return "Product not found", 404

    return render_template("product_detail.html", product=product.to_dict())

@bp.route("/api/<int:product_id>")
def product_api(product_id):
    product = Product.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    return jsonify(product.to_dict())
