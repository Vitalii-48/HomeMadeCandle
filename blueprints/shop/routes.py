# blueprints/shop/routes.py

from flask import render_template, request, redirect, url_for, jsonify, session
from extensions import db
from models import Product, Color, Order, OrderItem, Composition
from services.cart import CartService
from services.otp import generate_otp, verify_otp
from services.nova_poshta import search_cities, get_warehouses
from services.telegram import send_order_notification
from . import bp

from datetime import date


# ─────────────────────────────────────────────
# Допоміжна функція: ціна з урахуванням кольору
# price_modifier — відсоток надбавки (наприклад, 10 = +10% до базової ціни)
# ─────────────────────────────────────────────
def price_with_color(product, color):
    modifier = color.price_modifier if color else 0.0
    return round(product.price * (1 + modifier / 100))


# ─────────────────────────────────────────────
# Допоміжна функція: генерація номера замовлення
# Формат: YYYYMMDD-XXXX, де XXXX — порядковий номер за поточний день
# Приклад: 20260407-0003 (третє замовлення за 7 квітня 2026)
# ─────────────────────────────────────────────
def generate_order_number() -> str:
    today        = date.today()
    date_prefix  = today.strftime("%Y%m%d")
    like_pattern = f"{date_prefix}-%"
    count = db.session.query(db.func.count(Order.id)).filter(
        Order.order_number.like(like_pattern)
    ).scalar() or 0
    return f"{date_prefix}-{count + 1:04d}"


# ─────────────────────────────────────────────
# СТОРІНКА КОШИКА
# ─────────────────────────────────────────────
@bp.route("/cart")
def cart():
    # Зберігаємо звідки прийшов користувач для кнопки "Повернутись"
    # після location.reload() referrer вказує на сам кошик — ігноруємо
    cart_url = url_for('shop.cart')
    referrer = request.referrer or ''
    if referrer and cart_url not in referrer:
        session['cart_back_url'] = referrer
    back_url = session.get('cart_back_url') or url_for('public.catalog')

    cart  = CartService.get()
    items = []
    total = 0.0

    for i, it in enumerate(cart):

        # ── Товар ──
        if it.get("product_id"):
            product = db.session.get(Product, it["product_id"])
            if not product:
                continue
            color    = db.session.get(Color, it["color_id"]) if it.get("color_id") else None
            price    = it["unit_price"] if it["unit_price"] is not None else price_with_color(product, color)
            subtotal = price * it["quantity"]
            total   += subtotal
            cover    = product.images[0] if product.images else None
            items.append({
                "index":      i,
                "product":    product,
                "color":      color,
                "quantity":   it["quantity"],
                "unit_price": price,
                "subtotal":   subtotal,
                "cover":      cover,
            })

        # ── Композиція (набір свічок) ──
        else:
            composition = db.session.get(Composition, it.get("composition_id"))
            if not composition:
                continue
            subtotal = it["unit_price"] * it["quantity"]
            total   += subtotal
            cover    = composition.images[0] if composition.images else None
            items.append({
                "index":       i,
                "composition": composition,
                "quantity":    it["quantity"],
                "unit_price":  it["unit_price"],
                "subtotal":    subtotal,
                "cover":       cover,
            })

    return render_template("shop/cart.html", items=items, total=total, back_url=back_url)


# ─────────────────────────────────────────────
# ДОДАВАННЯ ТОВАРУ АБО КОМПОЗИЦІЇ ДО КОШИКА
# ─────────────────────────────────────────────
@bp.route("/cart/add", methods=["POST"])
def cart_add():
    data           = request.get_json()
    product_id     = data.get("product_id")
    composition_id = data.get("composition_id")

    if product_id:
        product  = db.get_or_404(Product, product_id)
        color_id = data.get("color_id")
        color    = db.session.get(Color, color_id) if color_id else None
        qty      = max(1, int(data.get("quantity", 1)))
        price    = price_with_color(product, color)
        CartService.add_product(product.id, color.id if color else None, qty, price)
        return jsonify({"ok": True, "cart_count": CartService.count()})

    if composition_id:
        composition = db.get_or_404(Composition, composition_id)
        qty         = max(1, int(data.get("quantity", 1)))
        CartService.add_composition(composition_id, qty, composition.price)
        return jsonify({"ok": True, "cart_count": CartService.count()})

    return jsonify({"ok": False, "error": "no item", "cart_count": CartService.count()})


# ─────────────────────────────────────────────
# ОНОВЛЕННЯ КІЛЬКОСТІ ПОЗИЦІЇ В КОШИКУ
# ─────────────────────────────────────────────
@bp.route("/cart/update/<int:index>", methods=["POST"])
def cart_update(index):
    qty = request.get_json().get("quantity", 1)
    CartService.update_quantity(index, qty)
    return jsonify({"ok": True})


# ─────────────────────────────────────────────
# ВИДАЛЕННЯ ПОЗИЦІЇ З КОШИКА
# ─────────────────────────────────────────────
@bp.route("/cart/remove/<int:index>", methods=["POST"])
def cart_remove(index):
    CartService.remove(index)
    return jsonify({"ok": True})


# ─────────────────────────────────────────────
# ОФОРМЛЕННЯ ЗАМОВЛЕННЯ
# ─────────────────────────────────────────────
@bp.route("/checkout", methods=["GET", "POST"])
def checkout():
    if request.method == "POST":
        form  = request.form
        cart  = CartService.get()
        phone = form.get("phone", "")

        # Перевіряємо що номер телефону верифіковано через OTP у цій сесії
        if session.get("phone_verified") != phone:
            return render_template("shop/checkout.html",
                                   error="Підтвердіть номер телефону")

        # Якщо кошик порожній — повертаємо назад без створення замовлення
        if not cart:
            return redirect(url_for("shop.cart"))

        # Генеруємо унікальний номер замовлення у форматі YYYYMMDD-XXXX
        order_number = generate_order_number()

        # Створюємо запис замовлення
        order = Order(
            order_number=order_number,
            customer_name=form.get("name"),
            phone=form.get("phone"),
            contact_method=form.get("contact_method"),
            comment=form.get("comment"),
            delivery_type=form.get("delivery_type"),
            np_city_name=form.get("np_city_name"),
            np_warehouse=form.get("np_warehouse"),
            status="new",
        )
        db.session.add(order)
        db.session.flush()  # Отримуємо order.id до commit для OrderItem

        # Додаємо позиції замовлення з кошика
        total = 0.0
        for it in cart:
            if it.get("product_id"):
                product = db.session.get(Product, it["product_id"])
                if not product:
                    continue
                color = db.session.get(Color, it["color_id"]) if it.get("color_id") else None
                price = it["unit_price"]
                db.session.add(OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    color_id=color.id if color else None,
                    quantity=it["quantity"],
                    unit_price=price,
                ))
                total += price * it["quantity"]

            elif it.get("composition_id"):
                composition = db.session.get(Composition, it["composition_id"])
                if not composition:
                    continue
                price = it["unit_price"]
                db.session.add(OrderItem(
                    order_id=order.id,
                    composition_id=composition.id,
                    quantity=it["quantity"],
                    unit_price=price,
                ))
                total += price * it["quantity"]

        order.total_amount = total
        db.session.commit()
        CartService.clear()

        # Відправляємо повідомлення в Telegram після успішного збереження.
        # Помилка відправки не скасовує замовлення (обробляється всередині сервісу).
        send_order_notification(order)

        return redirect(url_for("shop.order_success", order_id=order.id))

    return render_template("shop/checkout.html")


# ─────────────────────────────────────────────
# СТОРІНКА УСПІШНОГО ЗАМОВЛЕННЯ
# ─────────────────────────────────────────────
@bp.route("/order/success/<int:order_id>")
def order_success(order_id):
    order = db.get_or_404(Order, order_id)
    return render_template("shop/order_success.html", order=order)


# ─────────────────────────────────────────────
# OTP: ВІДПРАВКА КОДУ ВЕРИФІКАЦІЇ
# ─────────────────────────────────────────────
@bp.route("/verify/send", methods=["POST"])
def send_verification():
    phone = request.get_json().get("phone", "").strip()
    if not phone:
        return jsonify({"ok": False, "error": "Введіть номер"})
    code = generate_otp(phone)
    # ЕМУЛЯЦІЯ: в продакшні код надсилається через SMS-сервіс (Twilio тощо)
    return jsonify({"ok": True, "demo_code": code})


# ─────────────────────────────────────────────
# OTP: ПЕРЕВІРКА КОДУ ВЕРИФІКАЦІЇ
# Верифікований номер зберігається у сесії для checkout
# ─────────────────────────────────────────────
@bp.route("/verify/check", methods=["POST"])
def check_verification():
    data  = request.get_json()
    phone = data.get("phone", "")
    code  = data.get("code", "")
    if verify_otp(phone, code):
        session["phone_verified"] = phone
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "Невірний або прострочений код"})


# ─────────────────────────────────────────────
# НОВА ПОШТА: ПОШУК МІСТ
# Мінімум 2 символи для запиту (перевірка також у JS)
# ─────────────────────────────────────────────
@bp.route("/nova-poshta/cities")
def np_cities():
    query = request.args.get("q", "")
    if len(query) < 2:
        return jsonify([])
    return jsonify(search_cities(query))


# ─────────────────────────────────────────────
# НОВА ПОШТА: ВІДДІЛЕННЯ ЗА REF МІСТА
# ─────────────────────────────────────────────
@bp.route("/nova-poshta/warehouses")
def np_warehouses():
    city_ref = request.args.get("city_ref", "")
    if not city_ref:
        return jsonify([])
    return jsonify(get_warehouses(city_ref))