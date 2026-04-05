# models.py

from datetime import datetime
from flask_login import UserMixin
from extensions import db

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(64), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    wax_type = db.Column(db.String(64))
    category = db.Column(db.String(64))
    length = db.Column(db.Integer)
    width = db.Column(db.Integer)
    height = db.Column(db.Integer)
    weight = db.Column(db.Integer)

    price = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    colors = db.relationship("Color", backref="product", cascade="all, delete-orphan")
    images = db.relationship("ProductImage", backref="product",
                             order_by="ProductImage.sort_order",
                             cascade="all, delete-orphan")

    # Створення вільного SKU
    @staticmethod
    def get_next_sku():
        existing_skus = db.session.query(Product.sku).all()
        used = set()
        for s in existing_skus:
            try:
                used.add(int(s[0]))
            except (ValueError, TypeError):
                continue

        for i in range(1, len(used) + 2):
            if i not in used:
                return i
        return None


class Color(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    color_name = db.Column(db.String(64), nullable=False)
    color_hex = db.Column(db.String(7), nullable=False)  # "#FFFFFF"
    is_default = db.Column(db.Boolean, default=False)
    price_modifier = db.Column(db.Integer, default=0)     # надбавка до базової ціни при виборі кольору крім білого

    def to_dict(self):
        return {
            "id": self.id,
            "color_name": self.color_name,
            "color_hex": self.color_hex,
            "is_default": self.is_default,
            "price_modifier": self.price_modifier,
        }

class ProductImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    filename = db.Column(db.String(255), nullable=False)         # оригінал
    preview_filename = db.Column(db.String(255))                  # прев’ю 200x200
    alt_text = db.Column(db.String(120))
    sort_order = db.Column(db.Integer, default=0)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(120))
    phone = db.Column(db.String(32))
    contact_method = db.Column(db.String(32))  # "phone", "viber", "telegram"
    comment = db.Column(db.Text)
    total_amount = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(32), default="new")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship("OrderItem", backref="order", cascade="all, delete-orphan")
    delivery_type = db.Column(db.String(32))
    np_city_name = db.Column(db.String(120))
    np_warehouse = db.Column(db.String(255))

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=True)
    color_id = db.Column(db.Integer, db.ForeignKey("color.id"), nullable=True)
    composition_id = db.Column(db.Integer, db.ForeignKey("composition.id"), nullable=True)
    quantity = db.Column(db.Integer, default=1)
    unit_price = db.Column(db.Integer, default=0)

class Composition(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    image = db.Column(db.String(255))   # шлях до фото (filename)
    price = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    images = db.relationship("CompositionImage", backref="composition",
                             order_by="CompositionImage.sort_order",
                             cascade="all, delete-orphan")


class CompositionImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    composition_id = db.Column(db.Integer, db.ForeignKey("composition.id"), nullable=False)
    filename = db.Column(db.String(255), nullable=False)        # оригінал
    preview_filename = db.Column(db.String(255))                # прев’ю 200x200
    alt_text = db.Column(db.String(120))
    sort_order = db.Column(db.Integer, default=0)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)


class ColorPalette(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    color_name = db.Column(db.String(64), nullable=False)
    color_hex = db.Column(db.String(7), nullable=False)
    is_default = db.Column(db.Boolean, default=False)
    price_modifier = db.Column(db.Integer, default=0)
    sort_order = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            "id": self.id,
            "color_name": self.color_name,
            "color_hex": self.color_hex,
            "is_default": self.is_default,
            "price_modifier": self.price_modifier,
        }


class TelegramUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    chat_id = db.Column(db.BigInteger, unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


