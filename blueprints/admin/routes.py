# blueprints/admin/routes.py
import os
from flask import render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, login_user, logout_user
from werkzeug.security import check_password_hash
from extensions import db, login_manager
from models import Product, Color, ProductImage, Order, User, Composition
from services.images import save_image
from . import bp

# Головна сторінка адмінки
@bp.route("/")
@login_required
def admin_index():
  return render_template("admin/index.html")

# Завантаження користувача для Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

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
        if not product:
            product = Product()
            db.session.add(product)


        # 1. Основні дані продукту
        product.sku = request.form.get("sku")
        product.name = request.form.get("name")
        product.description = request.form.get("description")
        product.wax_type = request.form.get("wax_type")
        product.category = request.form.get("category")
        product.price = int(request.form.get("price") or 0)
        product.width = int(request.form.get("width") or 0)
        product.height = int(request.form.get("height") or 0)
        product.depth = int(request.form.get("depth") or 0)
        product.weight = int(request.form.get("weight") or 0)
        product.is_active = "is_active" in request.form

        db.session.flush() # Щоб отримати ID нового продукту

        # 2. Обробка кольорів (списки з форми)
        c_ids = request.form.getlist("color_id[]")
        c_names = request.form.getlist("color_name[]")
        c_hexes = request.form.getlist("color_hex[]")

        for c_id, name, hex_val in zip(c_ids, c_names, c_hexes):
            if not name.strip(): continue # пропускаємо порожні імена

            if c_id == "new":
                new_color = Color(product_id=product.id, color_name=name, color_hex=hex_val)
                db.session.add(new_color)
            else:
                existing_color = Color.query.get(int(c_id))
                if existing_color:
                    existing_color.color_name = name
                    existing_color.color_hex = hex_val

        # 3. Обробка зображень (множинне завантаження)
        files = request.files.getlist("image_file[]")
        print("FILES:", files)

        for file in files:
            if file and file.filename:
                try:
                    filename, preview = save_image(file)
                    img = ProductImage(product_id=product.id, filename=filename, preview_filename=preview)
                    db.session.add(img)
                except Exception as e:
                    flash(f"Помилка завантаження фото: {e}")

        db.session.commit()
        flash("Дані збережено!")
        return redirect(url_for("admin.product_edit", product_id=product.id))

    # Для відображення сторінки (GET)
    colors = Color.query.filter_by(product_id=product.id).all() if product else []
    images = ProductImage.query.filter_by(product_id=product.id).all() if product else []
    return render_template("admin/product_form.html", product=product, colors=colors, images=images)

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
    # шлях до файлу
    upload_folder = os.path.join(current_app.static_folder, "img/uploads")
    file_path = os.path.join(upload_folder, img.filename)
    preview_path = os.path.join(upload_folder, img.preview_filename)

    # пробуємо видалити основний файл
    if os.path.exists(file_path):
        os.remove(file_path)

    # пробуємо видалити прев’ю
    if os.path.exists(preview_path):
        os.remove(preview_path)

    # видаляємо запис з БД

    db.session.delete(img); db.session.commit()
    return {"status": "success"}

# Видалення продукту
@bp.route("/products/<int:product_id>/delete", methods=["POST"])
@login_required
def product_delete(product_id):
    product = Product.query.get_or_404(product_id)

    # Видаляємо пов’язані зображення з диску
    upload_folder = os.path.join(current_app.static_folder, "img/uploads")
    for img in ProductImage.query.filter_by(product_id=product.id).all():
        file_path = os.path.join(upload_folder, img.filename)
        preview_path = os.path.join(upload_folder, img.preview_filename)

        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists(preview_path):
            os.remove(preview_path)

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
        if file and file.filename:
            try:
                filename, preview = save_image(file)
            except Exception as e:
                flash(f"Помилка завантаження: {e}")
        price = request.form.get("price", 0)
        comp = Composition(title=title, description=description, image=filename, is_active=bool(request.form.get("is_active")))
        db.session.add(comp); db.session.commit()
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
                filename, preview = save_image(file)
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

    upload_folder = os.path.join(current_app.static_folder, "img/uploads")

    # основне зображення
    if comp.image:
        file_path = os.path.join(upload_folder, comp.image)
        if os.path.exists(file_path):
            os.remove(file_path)
        preview_name = f"preview_{comp.image}"
        preview_path = os.path.join(upload_folder, preview_name)
        if os.path.exists(preview_path):
            os.remove(preview_path)

    # видалення запису з БД

    db.session.delete(comp); db.session.commit()
    flash("Композицію успішно видалено!")
    return redirect(url_for("admin.composition_list"))