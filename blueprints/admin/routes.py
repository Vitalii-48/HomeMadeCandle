# blueprints/admin/routes.py

from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, login_user, logout_user
from werkzeug.security import check_password_hash
from extensions import db
from models import Product, Color, ProductImage, Order, User, Composition, CompositionImage, ColorPalette
from services.images import save_image, delete_images
from . import bp

# Головна сторінка адмінки
@bp.route("/")
@login_required
def admin_index():
  return render_template("admin/index.html")

# Авторизація (Login)
@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for("admin.admin_index"))
        flash("Невірний логін або пароль")
    return render_template("admin/login.html")

# Вихід із системи (Logout)
@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("admin.login"))

# Список товарів
@bp.route("/products")
@login_required
def product_list():
    products = Product.query.order_by(Product.name).all()
    return render_template("admin/product_list.html", products=products)


@bp.route("/products/edit", methods=["GET", "POST"])
@bp.route("/products/edit/<int:product_id>", methods=["GET", "POST"])
@login_required
def product_edit(product_id=None):
    product = Product.query.get(product_id) if product_id else None

    if request.method == "POST":
        is_new = product is None
        if is_new:
            product = Product()
            db.session.add(product)

        product.sku = request.form.get("sku")
        product.name = request.form.get("name")
        product.description = request.form.get("description")
        product.wax_type = request.form.get("wax_type")
        product.category = request.form.get("category")
        product.length = int(request.form.get("length") or 0)
        product.width = int(request.form.get("width") or 0)
        product.height = int(request.form.get("height") or 0)
        product.weight = int(request.form.get("weight") or 0)
        product.price = int(request.form.get("price") or 0)
        product.is_active = "is_active" in request.form

        db.session.flush()

        # ✏️ ЗМІНА: оновлення кольорів при збереженні
        color_ids = request.form.getlist("color_id[]")
        color_names = request.form.getlist("color_name[]")
        color_hexes = request.form.getlist("color_hex[]")

        for i, cid in enumerate(color_ids):
            name = color_names[i] if i < len(color_names) else ""
            hex_ = color_hexes[i] if i < len(color_hexes) else "#ffffff"
            # ✏️ ЗМІНА: читаємо модифікатор по індексу
            modifier = int(request.form.get(f"color_modifier_{i}") or 0)

            if cid == "new" or not cid or cid == "None":
                db.session.add(Color(
                    product_id=product.id,
                    color_name=name,
                    color_hex=hex_,
                    price_modifier=modifier,
                ))
            else:
                color = Color.query.get(int(cid))
                if color:
                    color.color_name = name
                    color.color_hex = hex_
                    color.price_modifier = modifier

        # ✏️ ЗМІНА: палітру копіюємо тільки якщо новий товар І кольорів не передано
        if is_new and not color_ids:
            palette = ColorPalette.query.order_by(ColorPalette.is_default.desc(), ColorPalette.sort_order).all()
            for j, p in enumerate(palette):
                db.session.add(Color(
                    product_id=product.id,
                    color_name=p.color_name,
                    color_hex=p.color_hex,
                    is_default=p.is_default,
                    price_modifier=p.price_modifier,
                ))



        files = request.files.getlist("images[]")
        max_order = db.session.query(
            db.func.max(ProductImage.sort_order)
        ).filter_by(product_id=product.id).scalar() or -1

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

    if product:
        colors = Color.query.filter_by(product_id=product.id).order_by(Color.is_default.desc()).all()
        for c in colors:
            print(f"Color: {c.color_name}, modifier: {c.price_modifier}")
        suggested_sku = product.sku

    else:
        # для нового товару показуємо палітру як дефолтні кольори
        palette = ColorPalette.query.order_by(ColorPalette.is_default.desc(), ColorPalette.sort_order).all()
        colors = [Color(color_name=p.color_name, color_hex=p.color_hex, price_modifier=p.price_modifier) for p in palette]
        suggested_sku = Product.get_next_sku()
    images = ProductImage.query.filter_by(product_id=product.id).order_by(ProductImage.sort_order).all() if product else []
    return render_template("admin/product_form.html", product=product, colors=colors, images=images, suggested_sku=suggested_sku)


@bp.route("/products/<int:product_id>/images/add", methods=["POST"])
@login_required
def image_add(product_id):
    files = request.files.getlist("images[]")

    # визначаємо поточний максимальний sort_order
    max_order = db.session.query(
        db.func.max(ProductImage.sort_order)
    ).filter_by(product_id=product_id).scalar() or -1

    saved = 0
    for i, file in enumerate(files):
        if file and file.filename:
            try:
                filename, preview = save_image(file)
                db.session.add(ProductImage(
                    product_id=product_id,
                    filename=filename,
                    preview_filename=preview,
                    sort_order=max_order + 1 + i  # перше = наступний після існуючих
                ))
                saved += 1
            except Exception as e:
                flash(f"Помилка завантаження {file.filename}: {e}")

    if saved:
        db.session.commit()
        flash(f"Додано {saved} фото.")
    return redirect(url_for("admin.product_edit", product_id=product_id))


# API для швидкого видалення елементів (викликається через JS)
@bp.route("/colors/<int:color_id>/delete", methods=["POST"])
@login_required
def color_delete(color_id):
    c = Color.query.get_or_404(color_id)
    db.session.delete(c); db.session.commit()
    return {"status": "success"}

@bp.route("/images/<int:image_id>/delete", methods=["POST"])
@login_required
def image_delete(image_id):
    img = ProductImage.query.get_or_404(image_id)
    delete_images([img.filename, img.preview_filename])
    db.session.delete(img)
    db.session.commit()
    return {"status": "success"}

# Видалення продукту
@bp.route("/products/<int:product_id>/delete", methods=["POST"])
@login_required
def product_delete(product_id):
    product = Product.query.get_or_404(product_id)

    # Видаляємо пов’язані зображення з диску
    for img in ProductImage.query.filter_by(product_id=product.id).all():
        delete_images([img.filename, img.preview_filename])
        db.session.delete(img)

    # Видаляємо пов’язані кольори
    Color.query.filter_by(product_id=product.id).delete()
    db.session.delete(product)
    db.session.commit()
    flash("Продукт успішно видалено!")
    return redirect(url_for("admin.product_list"))

# Список замовлень
@bp.route("/orders")
@login_required
def order_list():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template("admin/order_list.html", orders=orders)

# CRUD для Composition
@bp.route("/compositions")
@login_required
def composition_list():
    compositions = Composition.query.order_by(Composition.created_at.desc()).all()
    return render_template("admin/composition_list.html", compositions=compositions)

@bp.route("/compositions/new", methods=["GET", "POST"])
@login_required
def composition_new():
    if request.method == "POST":
        title = request.form["title"]
        description = request.form.get("description")
        file = request.files.get("image")
        filename = None
        comp = Composition(
            title=title,
            description=description,
            image=filename,
            is_active=bool(request.form.get("is_active")),
            price=int(request.form.get("price", 0)))
        db.session.add(comp)
        db.session.flush()
        if file and file.filename:
            try:
                filename, preview = save_image(file)
                img = CompositionImage(composition_id=comp.id,
                                       filename=filename,
                                       preview_filename=preview)
                db.session.add(img)
                comp.image = filename
            except Exception as e:
                flash(f"Помилка завантаження: {e}")

        db.session.commit()
        return redirect(url_for("admin.composition_list"))
    return render_template("admin/composition_form.html", composition=None)

@bp.route("/compositions/<int:comp_id>/edit", methods=["GET", "POST"])
@login_required
def composition_edit(comp_id):
    comp = Composition.query.get_or_404(comp_id)
    if request.method == "POST":
        comp.title = request.form.get("title", comp.title)
        comp.description = request.form.get("description", comp.description)
        comp.is_active = bool(request.form.get("is_active"))
        comp.price = request.form.get("price", comp.price)
        file = request.files.get("image")
        if file and file.filename:
            try:
                # видаляємо старе фото з диску
                if comp.image:
                    delete_images([comp.image, f"preview_{comp.image}"])

                # зберігаємо нове
                filename, preview = save_image(file)
                img = CompositionImage(composition_id=comp.id,
                                       filename=filename,
                                       preview_filename=preview)
                db.session.add(img)
                comp.image = filename
            except Exception as e:
                flash(f"Помилка завантаження: {e}")
        db.session.commit()
        return redirect(url_for("admin.composition_list"))
    return render_template("admin/composition_form.html", composition=comp)

@bp.route("/compositions/<int:comp_id>/delete", methods=["POST"])
@login_required
def composition_delete(comp_id):
    comp = Composition.query.get_or_404(comp_id)

    # основне зображення
    if comp.image:
        delete_images([comp.image, f"preview_{comp.image}"])

    # видалення запису з БД
    db.session.delete(comp); db.session.commit()
    flash("Композицію успішно видалено!")
    return redirect(url_for("admin.composition_list"))

# --- маршрути палітри ---

@bp.route("/palette")
@login_required
def palette_list():
    palette = ColorPalette.query.order_by(ColorPalette.sort_order).all()
    return render_template("admin/palette.html", palette=palette)

@bp.route("/palette/add", methods=["POST"])
@login_required
def palette_add():
    is_default = "is_default" in request.form
    if is_default:
        ColorPalette.query.update({"is_default": False})
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

@bp.route("/palette/<int:color_id>/delete", methods=["POST"])
@login_required
def palette_delete(color_id):
    c = ColorPalette.query.get_or_404(color_id)
    db.session.delete(c)
    db.session.commit()
    return redirect(url_for("admin.palette_list"))


# маршрут для збереження порядку:
@bp.route("/images/reorder", methods=["POST"])
@login_required
def images_reorder():
    order = request.get_json().get("order", [])
    for i, image_id in enumerate(order):
        ProductImage.query.filter_by(id=int(image_id)).update({"sort_order": i})
    db.session.commit()
    return jsonify({"ok": True})

