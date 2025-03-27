from flask import Blueprint, render_template, jsonify, request, current_app
from app.models.product import Product
from app.db import db 

bp = Blueprint("product", __name__, url_prefix="/products")

@bp.route("/")
def product_list():
    rows = current_app.db.execute("SELECT category_id, category_name FROM Products_Categories")
    categories = [{"id": id, "name": name} for (id, name) in rows]

    print("[DEBUG] categories from DB:", categories)

    k_str = request.args.get("k")
    try:
        k = int(k_str)
    except (TypeError, ValueError):
        k = None


    try:
        category_id = int(request.args.get('category_id'))
    except (TypeError, ValueError):
        category_id = None

    print(f"[DEBUG] category_id = {category_id}, k = {k}")

    products = Product.get_all_with_min_price(k=k, category_id=category_id)

    return render_template("products.html", products=products, categories=categories)


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