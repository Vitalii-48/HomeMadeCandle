# blueprints/shop/routes.py

from flask import render_template, request, redirect, url_for, jsonify
from extensions import db
from models import Product, Color, Order, OrderItem, Composition
from services.cart import CartService
from . import bp

# Допоміжна функція для ціни з урахуванням кольору
def price_with_color(product, color):
    # Якщо колір має ціновий модифікатор, додаємо його до базової ціни
    modifier = color.price_modifier if color else 0.0
    return round(product.price * (1 + modifier/100))

# Сторінка кошика
@bp.route("/cart")
def cart():
    referrer = request.referrer or url_for('public.catalog')
    cart = CartService.get()
    items = []
    total = 0.0
    for i, it in enumerate(cart):
        if it.get("product_id"):
            product = Product.query.get(it["product_id"])
            if not product:
                continue
            color = Color.query.get(it.get("color_id")) if it.get("color_id") else None
            price = it["unit_price"] or price_with_color(product, color)
            subtotal = price * it["quantity"]
            total += subtotal
            cover = product.images[0] if product.images else None
            items.append({
                "index": i,
                "product": product,
                "color": color,
                "quantity": it["quantity"],
                "unit_price": price,
                "subtotal": subtotal,
                "cover": cover
            })

        else:
            composition = Composition.query.get(it["composition_id"])
            if not composition:
                continue
            subtotal = it["unit_price"] * it["quantity"]
            total += subtotal
            cover = composition.images[0] if composition.images else None
            items.append({
                "index": i,
                "composition": composition,
                "quantity": it["quantity"],
                "unit_price": it["unit_price"],
                "subtotal": subtotal,
                "cover": cover
            })

    return render_template("shop/cart.html", items=items, total=total, back_url=referrer)

# Додавання товару до кошика
@bp.route("/cart/add", methods=["POST"])
def cart_add():
    data = request.get_json()
    product_id = data.get("product_id")
    composition_id = data.get("composition_id")

    if product_id:
        product = Product.query.get_or_404(data["product_id"])
        color_id = data.get("color_id")
        color = Color.query.get(color_id) if color_id else None
        qty = max(1, int(data.get("quantity", 1)))
        price = price_with_color(product, color)
        CartService.add_product(product.id, color.id if color else None, qty, price)
        return jsonify({"ok": True})

    if composition_id:
        composition = Composition.query.get_or_404(composition_id)
        qty = max(1, int(data.get("quantity", 1)))
        CartService.add_composition(composition_id, qty, composition.price)
        return jsonify({"ok": True})

    return jsonify({"ok": False, "error": "no item"})

# Оновлення кількості товару в кошику
@bp.route("/cart/update/<int:index>", methods=["POST"])
def cart_update(index):
    qty = request.get_json().get("quantity", 1)
    CartService.update_quantity(index, qty)
    return jsonify({"ok": True})

# Видалення товару з кошика
@bp.route("/cart/remove/<int:index>", methods=["POST"])
def cart_remove(index):
    CartService.remove(index)
    return jsonify({"ok": True})

@bp.route("/checkout", methods=["GET", "POST"])
def checkout():
    if request.method == "POST":
        form = request.form
        cart = CartService.get()
        if not cart:
            # Якщо кошик порожній — повертаємо на сторінку кошика
            return redirect(url_for("shop.cart"))

        # Створюємо нове замовлення
        order = Order(
            customer_name=form.get("name"),
            phone=form.get("phone"),
            contact_method=form.get("contact_method"),
            address=form.get("address"),
            comment=form.get("comment"),
            status="new",
        )
        db.session.add(order)
        db.session.flush()

        # Додаємо товари до замовлення
        total = 0.0
        for it in cart:
            if it.get("product_id"):
                product = Product.query.get(it["product_id"])
                color = Color.query.get(it.get("color_id")) if it.get("color_id") else None
                if not product:
                    continue
                price = it["unit_price"]
                db.session.add(OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    color_id=color.id if color else None,
                    quantity=it["quantity"],
                    unit_price=price
                ))
                total += price * it["quantity"]

            elif it.get("composition_id"):
                composition = Composition.query.get(it["composition_id"])
                if not composition:
                    continue
                price = it["unit_price"]
                db.session.add(OrderItem(
                    order_id=order.id,
                    composition_id=composition.id,
                    quantity=it["quantity"],
                    unit_price=price
                ))
                total += price * it["quantity"]

        # Записуємо загальну суму замовлення
        order.total_amount = total
        db.session.commit()
        CartService.clear()
        return redirect(url_for("shop.order_success", order_id=order.id))

    return render_template("shop/checkout.html")

# Сторінка успішного замовлення
@bp.route("/order/success/<int:order_id>")
def order_success(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template("shop/order_success.html", order=order)