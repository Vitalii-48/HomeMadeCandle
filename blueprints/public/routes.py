# blueprints/public/routes.py

from sqlalchemy import select
from sqlalchemy.orm import joinedload
from flask import render_template
from models import Product, Composition
from extensions import db
from blueprints.public import bp

# Головна сторінка сайту
@bp.route("/")
def index():
    # Вибираємо всі активні композиції з БД, сортуємо за датою створення (новіші першими)
    compositions = db.session.scalars(
        select(Composition)
        .where(Composition.is_active == True)
        .order_by(Composition.created_at.desc())
    ).all()
    products = db.session.scalars(
        select(Product)
        .where(Product.is_active == True)
        .options(joinedload(Product.images))
    ).unique().all()
    return render_template("public/index.html", products=products, compositions=compositions)

# Сторінка зі списком композицій
@bp.route("/compositions")
def compositions():
    compositions = db.session.scalars(
        select(Composition)
        .where(Composition.is_active == True)
        .order_by(Composition.created_at.desc())
    ).all()
    return render_template("public/compositions.html", compositions=compositions)

# Сторінка FAQ (часті питання)
@bp.route("/faq")
def faq():
    return render_template("public/faq.html")

# Каталог товарів
@bp.route("/catalog")
def catalog():
    products = db.session.scalars(
        select(Product)
        .where(Product.is_active == True)
        .options(joinedload(Product.images), joinedload(Product.colors))
    ).unique().all()
    for product in products:
        product.colors_list = [c.to_dict() for c in product.colors]
    return render_template("public/catalog.html", products=products)

# Детальна сторінка товару
@bp.route("/product/<int:product_id>")
def product_detail(product_id):
    product = db.get_or_404(Product, product_id)
    colors = [c.to_dict() for c in product.colors]
    return render_template("public/product_detail.html", product=product, colors=colors)

# Політика конфіденційності
@bp.route("/privacy")
def privacy():
    return render_template("public/privacy.html")