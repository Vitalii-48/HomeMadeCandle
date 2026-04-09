# blueprints/admin/routes.py

from sqlalchemy import select, update, func
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, login_user, logout_user
from werkzeug.security import check_password_hash
from extensions import db
from models import Product, Color, ProductImage, Order, OrderItem, User, Composition, CompositionImage, ColorPalette
from services.images import save_image, delete_images
from . import bp


# ─────────────────────────────────────────────
# Головна сторінка адмінки
# ─────────────────────────────────────────────
@bp.route("/")
@login_required
def admin_index():
    return render_template("admin/index.html")


# ─────────────────────────────────────────────
# Авторизація
# ─────────────────────────────────────────────
@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email    = request.form.get("email")
        password = request.form.get("password")
        user = db.session.scalar(
            select(User).where(User.email == email)
        )
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for("admin.admin_index"))
        flash("Невірний логін або пароль")
    return render_template("admin/login.html")


# ─────────────────────────────────────────────
# Вихід із системи
# ─────────────────────────────────────────────
@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("admin.login"))


# ─────────────────────────────────────────────
# Список товарів
# ─────────────────────────────────────────────
@bp.route("/products")
@login_required
def product_list():
    products = db.session.scalars(
        select(Product).order_by(Product.name)
    ).all()
    return render_template("admin/product_list.html", products=products)


# ─────────────────────────────────────────────
# Створення / редагування товару
# ─────────────────────────────────────────────
@bp.route("/products/edit", methods=["GET", "POST"])
@bp.route("/products/edit/<int:product_id>", methods=["GET", "POST"])
@login_required
def product_edit(product_id=None):
    product = db.session.get(Product, product_id) if product_id else None

    if request.method == "POST":
        is_new = product is None
        if is_new:
            product = Product()
            db.session.add(product)

        # Основні поля товару
        product.sku         = request.form.get("sku")
        product.name        = request.form.get("name")
        product.description = request.form.get("description")
        product.wax_type    = request.form.get("wax_type")
        product.category    = request.form.get("category")
        product.length      = int(request.form.get("length")  or 0)
        product.width       = int(request.form.get("width")   or 0)
        product.height      = int(request.form.get("height")  or 0)
        product.weight      = int(request.form.get("weight")  or 0)
        product.price       = int(request.form.get("price")   or 0)
        product.is_active   = "is_active" in request.form

        db.session.flush()  # Отримуємо product.id до commit

        # Оновлення кольорів товару
        color_ids   = request.form.getlist("color_id[]")
        color_names = request.form.getlist("color_name[]")
        color_hexes = request.form.getlist("color_hex[]")

        for i, cid in enumerate(color_ids):
            name     = color_names[i] if i < len(color_names) else ""
            hex_     = color_hexes[i] if i < len(color_hexes) else "#ffffff"
            modifier = int(request.form.get(f"color_modifier_{i}") or 0)

            if cid in ("new", "", "None"):
                db.session.add(Color(
                    product_id=product.id,
                    color_name=name,
                    color_hex=hex_,
                    price_modifier=modifier,
                    is_default=False,
                ))
            else:
                color = db.session.get(Color, int(cid))
                if color:
                    color.color_name     = name
                    color.color_hex      = hex_
                    color.price_modifier = modifier

        # Копіюємо палітру як дефолтні кольори тільки для нового товару без кольорів
        if is_new and not color_ids:
            palette = db.session.scalars(
                select(ColorPalette).order_by(
                    ColorPalette.is_default.desc(), ColorPalette.sort_order
                )
            ).all()
            for p in palette:
                db.session.add(Color(
                    product_id=product.id,
                    color_name=p.color_name,
                    color_hex=p.color_hex,
                    is_default=p.is_default,
                    price_modifier=p.price_modifier,
                ))

        # Збереження завантажених зображень
        files = request.files.getlist("images[]")
        max_order = db.session.scalar(
            select(func.max(ProductImage.sort_order))
            .where(ProductImage.product_id == product.id)
        ) or -1

        for i, file in enumerate(files):
            if file and file.filename:
                try:
                    filename, preview = save_image(file)
                    db.session.add(ProductImage(
                        product_id=product.id,
                        filename=filename,
                        preview_filename=preview,
                        sort_order=max_order + 1 + i
                    ))
                except Exception as e:
                    flash(f"Помилка завантаження {file.filename}: {e}")

        db.session.commit()
        flash("Дані збережено!")
        return redirect(url_for("admin.product_edit", product_id=product.id))

    # GET: підготовка даних для форми
    if product:
        colors = db.session.scalars(
            select(Color)
            .where(Color.product_id == product.id)
            .order_by(Color.is_default.desc(), Color.id)
        ).all()
        suggested_sku = product.sku
    else:
        # Для нового товару показуємо палітру як дефолтні кольори
        palette = db.session.scalars(
            select(ColorPalette).order_by(
                ColorPalette.is_default.desc(), ColorPalette.sort_order
            )
        ).all()
        colors = [
            Color(color_name=p.color_name, color_hex=p.color_hex, price_modifier=p.price_modifier)
            for p in palette
        ]
        suggested_sku = Product.get_next_sku()

    images = db.session.scalars(
        select(ProductImage)
        .where(ProductImage.product_id == product.id)
        .order_by(ProductImage.sort_order)
    ).all() if product else []

    return render_template(
        "admin/product_form.html",
        product=product, colors=colors, images=images, suggested_sku=suggested_sku
    )


# ─────────────────────────────────────────────
# Додавання зображень до існуючого товару
# ─────────────────────────────────────────────
@bp.route("/products/<int:product_id>/images/add", methods=["POST"])
@login_required
def image_add(product_id):
    files = request.files.getlist("images[]")
    max_order = db.session.scalar(
        select(func.max(ProductImage.sort_order))
        .where(ProductImage.product_id == product_id)
    ) or -1

    saved = 0
    for i, file in enumerate(files):
        if file and file.filename:
            try:
                filename, preview = save_image(file)
                db.session.add(ProductImage(
                    product_id=product_id,
                    filename=filename,
                    preview_filename=preview,
                    sort_order=max_order + 1 + i
                ))
                saved += 1
            except Exception as e:
                flash(f"Помилка завантаження {file.filename}: {e}")

    if saved:
        db.session.commit()
        flash(f"Додано {saved} фото.")
    return redirect(url_for("admin.product_edit", product_id=product_id))


# ─────────────────────────────────────────────
# API: видалення кольору (без перезавантаження)
# ─────────────────────────────────────────────
@bp.route("/colors/<int:color_id>/delete", methods=["POST"])
@login_required
def color_delete(color_id):
    c = db.get_or_404(Color, color_id)
    db.session.delete(c)
    db.session.commit()
    return jsonify({"status": "success"})


# ─────────────────────────────────────────────
# API: видалення зображення (без перезавантаження)
# ─────────────────────────────────────────────
@bp.route("/images/<int:image_id>/delete", methods=["POST"])
@login_required
def image_delete(image_id):
    img = db.get_or_404(ProductImage, image_id)
    delete_images([img.filename, img.preview_filename])
    db.session.delete(img)
    db.session.commit()
    return jsonify({"status": "success"})


# ─────────────────────────────────────────────
# Видалення товару
# ─────────────────────────────────────────────
@bp.route("/products/<int:product_id>/delete", methods=["POST"])
@login_required
def product_delete(product_id):
    product = db.get_or_404(Product, product_id)

    # Знаходимо всі кольори цього продукту
    colors = db.session.scalars(
        select(Color).where(Color.product_id == product.id)
    ).all()
    color_ids = [c.id for c in colors]

    # Обнуляємо color_id в замовленнях які містять ці кольори
    if color_ids:
        db.session.execute(
            OrderItem.__table__.update()
            .where(OrderItem.color_id.in_(color_ids))
            .values(color_id=None)
        )

    # Видаляємо файли зображень з диску, потім записи з БД
    images = db.session.scalars(
        select(ProductImage).where(ProductImage.product_id == product.id)
    ).all()
    for img in images:
        delete_images([img.filename, img.preview_filename])
        db.session.delete(img)

    # Видаляємо кольори товару
    for color in colors:  # colors вже є зверху
        db.session.delete(color)

    db.session.delete(product)
    db.session.commit()
    flash("Продукт успішно видалено!")
    return redirect(url_for("admin.product_list"))


# ─────────────────────────────────────────────
# Список замовлень
# ─────────────────────────────────────────────
@bp.route("/orders")
@login_required
def order_list():
    orders = db.session.scalars(
        select(Order).order_by(Order.created_at.desc())
    ).all()
    return render_template("admin/order_list.html", orders=orders)


# ─────────────────────────────────────────────
# Позначення замовлення як "Відправлене"
# ─────────────────────────────────────────────
@bp.route("/orders/<int:order_id>/mark_sent", methods=["POST"])
@login_required
def order_mark_sent(order_id):
    order = db.get_or_404(Order, order_id)
    order.status = "sent"
    db.session.commit()
    flash(f"Замовлення #{order.order_number} позначено як відправлене.")
    return redirect(url_for("admin.order_list"))


# ─────────────────────────────────────────────
# Видалення замовлення
# ─────────────────────────────────────────────
@bp.route("/orders/<int:order_id>/delete", methods=["POST"])
@login_required
def order_delete(order_id):
    order = db.get_or_404(Order, order_id)
    db.session.delete(order)
    db.session.commit()
    flash(f"Замовлення #{order.order_number} видалено.")
    return redirect(url_for("admin.order_list"))


# ─────────────────────────────────────────────
# Список композицій
# ─────────────────────────────────────────────
@bp.route("/compositions")
@login_required
def composition_list():
    compositions = db.session.scalars(
        select(Composition).order_by(Composition.created_at.desc())
    ).all()
    return render_template("admin/composition_list.html", compositions=compositions)


# ─────────────────────────────────────────────
# Створення композиції
# ─────────────────────────────────────────────
@bp.route("/compositions/new", methods=["GET", "POST"])
@login_required
def composition_new():
    if request.method == "POST":
        comp = Composition(
            title=request.form["title"],
            description=request.form.get("description"),
            image=None,
            is_active=bool(request.form.get("is_active")),
            price=int(request.form.get("price", 0))
        )
        db.session.add(comp)
        db.session.flush()

        file = request.files.get("image")
        if file and file.filename:
            try:
                filename, preview = save_image(file)
                db.session.add(CompositionImage(
                    composition_id=comp.id,
                    filename=filename,
                    preview_filename=preview
                ))
                comp.image = filename
            except Exception as e:
                flash(f"Помилка завантаження: {e}")

        db.session.commit()
        return redirect(url_for("admin.composition_list"))
    return render_template("admin/composition_form.html", composition=None)


# ─────────────────────────────────────────────
# Редагування композиції
# ─────────────────────────────────────────────
@bp.route("/compositions/<int:comp_id>/edit", methods=["GET", "POST"])
@login_required
def composition_edit(comp_id):
    comp = db.get_or_404(Composition, comp_id)
    if request.method == "POST":
        comp.title       = request.form.get("title", comp.title)
        comp.description = request.form.get("description", comp.description)
        comp.is_active   = bool(request.form.get("is_active"))
        comp.price       = int(request.form.get("price", comp.price) or 0)

        file = request.files.get("image")
        if file and file.filename:
            try:
                if comp.image:
                    delete_images([comp.image, f"preview_{comp.image}"])
                filename, preview = save_image(file)
                db.session.add(CompositionImage(
                    composition_id=comp.id,
                    filename=filename,
                    preview_filename=preview
                ))
                comp.image = filename
            except Exception as e:
                flash(f"Помилка завантаження: {e}")

        db.session.commit()
        return redirect(url_for("admin.composition_list"))
    return render_template("admin/composition_form.html", composition=comp)


# ─────────────────────────────────────────────
# Видалення композиції
# ─────────────────────────────────────────────
@bp.route("/compositions/<int:comp_id>/delete", methods=["POST"])
@login_required
def composition_delete(comp_id):
    comp = db.get_or_404(Composition, comp_id)
    if comp.image:
        delete_images([comp.image, f"preview_{comp.image}"])
    db.session.delete(comp)
    db.session.commit()
    flash("Композицію успішно видалено!")
    return redirect(url_for("admin.composition_list"))


# ─────────────────────────────────────────────
# Палітра кольорів — список
# ─────────────────────────────────────────────
@bp.route("/palette")
@login_required
def palette_list():
    palette = db.session.scalars(
        select(ColorPalette).order_by(ColorPalette.sort_order)
    ).all()
    return render_template("admin/palette.html", palette=palette)


# ─────────────────────────────────────────────
# Палітра кольорів — додавання
# ─────────────────────────────────────────────
@bp.route("/palette/add", methods=["POST"])
@login_required
def palette_add():
    is_default = "is_default" in request.form
    if is_default:
        # Скидаємо попередній дефолтний колір перед встановленням нового
        db.session.execute(
            update(ColorPalette).values(is_default=False)
        )
        db.session.flush()
    db.session.add(ColorPalette(
        color_name=request.form["color_name"],
        color_hex=request.form["color_hex"],
        price_modifier=int(request.form.get("price_modifier") or 0),
        is_default=is_default,
        sort_order=int(request.form.get("sort_order") or 0)
    ))
    db.session.commit()
    return redirect(url_for("admin.palette_list"))


# ─────────────────────────────────────────────
# Палітра кольорів — видалення
# ─────────────────────────────────────────────
@bp.route("/palette/<int:color_id>/delete", methods=["POST"])
@login_required
def palette_delete(color_id):
    c = db.get_or_404(ColorPalette, color_id)
    db.session.delete(c)
    db.session.commit()
    return redirect(url_for("admin.palette_list"))


# ─────────────────────────────────────────────
# API: збереження порядку зображень після drag & drop
# ─────────────────────────────────────────────
@bp.route("/images/reorder", methods=["POST"])
@login_required
def images_reorder():
    order = request.get_json().get("order", [])
    for i, image_id in enumerate(order):
        db.session.execute(
            update(ProductImage)
            .where(ProductImage.id == int(image_id))
            .values(sort_order=i)
        )
    db.session.commit()
    return jsonify({"ok": True})