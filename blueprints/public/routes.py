# blueprints/public/routes.py

from sqlalchemy.orm import joinedload
from flask import render_template
from models import Product, Composition
from blueprints.public import bp

# Головна сторінка сайту
@bp.route("/")
def index():
    # Вибираємо всі активні композиції з БД, сортуємо за датою створення (новіші першими)
    compositions = Composition.query.filter_by(is_active=True).order_by(Composition.created_at.desc()).all()
    products = Product.query.filter_by(is_active=True).options(joinedload(Product.images)).all()
    return render_template("public/index.html", products=products, compositions=compositions)

# Сторінка зі списком композицій
@bp.route("/compositions")
def compositions():
    compositions = Composition.query.filter_by(is_active=True).order_by(Composition.created_at.desc()).all()
    return render_template("public/compositions.html", compositions=compositions)

# Сторінка FAQ (часті питання)
@bp.route("/faq")
def faq():
    return render_template("public/faq.html")

# Каталог товарів
@bp.route("/catalog")
def catalog():
    products = Product.query.filter_by(is_active=True).options(joinedload(Product.images)).all()
    for product in products:
        product.colors_list = [c.to_dict() for c in product.colors]
    return render_template("public/catalog.html", products=products)

# Детальна сторінка товару
@bp.route("/product/<int:product_id>")
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    colors = [c.to_dict() for c in product.colors]
    return render_template("public/product_detail.html", product=product, colors=colors)