# models.py
# Визначення моделей бази даних (SQLAlchemy ORM).
# Кожен клас відповідає одній таблиці в БД.

from datetime import datetime, timezone
from flask_login import UserMixin
from extensions import db


class Product(db.Model):
    """
    Товар (свічка).

    Містить базову інформацію про товар: назву, опис, розміри, ціну,
    а також пов'язані кольори та зображення.
    """

    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(64), unique=True, nullable=False)        # Артикул товару
    name = db.Column(db.String(120), nullable=False)                   # Назва
    description = db.Column(db.Text)                                   # Опис
    wax_type = db.Column(db.String(64))                                # Тип воску
    category = db.Column(db.String(64))                                # Категорія

    # Розміри в міліметрах
    length = db.Column(db.Integer)
    width = db.Column(db.Integer)
    height = db.Column(db.Integer)
    weight = db.Column(db.Integer)                                     # Вага в грамах

    price = db.Column(db.Integer, default=0)                          # Ціна в копійках/гривнях
    is_active = db.Column(db.Boolean, default=True)                   # Чи відображається в каталозі

    # Зв'язок з кольорами: за замовчуванням — перший, решта за sort_order
    colors = db.relationship(
        "Color",
        backref="product",
        order_by="Color.is_default.desc(), Color.id",
        cascade="all, delete-orphan",
        lazy="select",
    )

    # Зв'язок із зображеннями: сортування за sort_order
    images = db.relationship(
        "ProductImage",
        backref="product",
        order_by="ProductImage.sort_order",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self):
        return f"<Product id={self.id} sku={self.sku} name={self.name!r}>"

    @staticmethod
    def get_next_sku():
        """
        Генерує наступний вільний числовий SKU.

        Перебирає всі існуючі SKU, знаходить найменше ціле число,
        яке ще не зайняте. Підходить для невеликих каталогів.

        Returns:
            int | None: вільний номер SKU або None (теоретично недосяжно).
        """
        existing_skus = db.session.query(Product.sku).all()
        used = set()
        for (sku,) in existing_skus:
            try:
                used.add(int(sku))
            except (ValueError, TypeError):
                continue  # Ігноруємо нечислові SKU

        # Шукаємо перший пропуск у послідовності
        for i in range(1, len(used) + 2):
            if i not in used:
                return i
        return None


class Color(db.Model):
    """
    Колір конкретного товару.

    Кожен товар може мати кілька кольорів; один з них позначається як default.
    price_modifier дозволяє додавати надбавку до базової ціни товару.
    """

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    color_name = db.Column(db.String(64), nullable=False)       # Назва кольору (наприклад, "Білий")
    color_hex = db.Column(db.String(7), nullable=False)         # HEX-код (#FFFFFF)
    is_default = db.Column(db.Boolean, default=False)           # Колір за замовчуванням
    sort_order = db.Column(db.Integer, default=0)               # Порядок відображення
    price_modifier = db.Column(db.Integer, default=0)           # Надбавка до ціни (у тих самих одиницях, що й price)

    def __repr__(self):
        return f"<Color id={self.id} name={self.color_name!r} hex={self.color_hex}>"

    def to_dict(self):
        """Серіалізація у словник для JSON-відповідей (наприклад, AJAX)."""
        return {
            "id": self.id,
            "color_name": self.color_name,
            "color_hex": self.color_hex,
            "is_default": self.is_default,
            "price_modifier": self.price_modifier,
        }


class ProductImage(db.Model):
    """
    Зображення товару.

    Зберігає ім'я файлу оригіналу та прев'ю (200×200).
    Фізичні файли лежать у UPLOAD_FOLDER.
    """

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    filename = db.Column(db.String(255), nullable=False)        # Оригінальне зображення
    preview_filename = db.Column(db.String(255))                # Прев'ю 200×200 (для каталогу)
    alt_text = db.Column(db.String(120))                        # Alt-текст для SEO / доступності
    sort_order = db.Column(db.Integer, default=0)               # Порядок у галереї

    def __repr__(self):
        return f"<ProductImage id={self.id} file={self.filename!r}>"


class Order(db.Model):
    """
    Замовлення покупця.

    Містить контактні дані, спосіб доставки та посилання на позиції замовлення.
    """

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True, nullable=True, index=True)  # Публічний номер замовлення
    customer_name = db.Column(db.String(120))
    phone = db.Column(db.String(32))
    contact_method = db.Column(db.String(32))   # Канал зв'язку: "phone" | "viber" | "telegram"
    comment = db.Column(db.Text)                # Коментар покупця
    total_amount = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(32), default="new")            # Статус: new / processing / done / cancelled
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Спосіб та деталі доставки (Нова Пошта)
    delivery_type = db.Column(db.String(32))
    np_city_name = db.Column(db.String(120))
    np_warehouse = db.Column(db.String(255))

    items = db.relationship("OrderItem", backref="order", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Order id={self.id} number={self.order_number!r} status={self.status!r}>"


class OrderItem(db.Model):
    """
    Позиція замовлення.

    Може посилатися або на товар (product_id + color_id),
    або на готову композицію (composition_id) — але не на обидва одночасно.
    """

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=True)
    color_id = db.Column(db.Integer, db.ForeignKey("color.id"), nullable=True)
    composition_id = db.Column(db.Integer, db.ForeignKey("composition.id"), nullable=True)
    quantity = db.Column(db.Integer, default=1)
    unit_price = db.Column(db.Integer, default=0)   # Ціна на момент оформлення (фіксується)

    product = db.relationship("Product", backref="order_items")
    color = db.relationship("Color", backref="order_items")
    composition = db.relationship("Composition", backref="order_items")

    def __repr__(self):
        return f"<OrderItem id={self.id} order_id={self.order_id} qty={self.quantity}>"


class Composition(db.Model):
    """
    Готова композиція зі свічок.

    Продається як єдиний товар; може мати власну галерею зображень.
    """

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    image = db.Column(db.String(255))               # Головне фото (filename) — застаріле поле, замінене images
    price = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    images = db.relationship(
        "CompositionImage",
        backref="composition",
        order_by="CompositionImage.sort_order",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self):
        return f"<Composition id={self.id} title={self.title!r}>"


class CompositionImage(db.Model):
    """Зображення композиції (аналог ProductImage для Composition)."""

    id = db.Column(db.Integer, primary_key=True)
    composition_id = db.Column(db.Integer, db.ForeignKey("composition.id"), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    preview_filename = db.Column(db.String(255))
    alt_text = db.Column(db.String(120))
    sort_order = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f"<CompositionImage id={self.id} file={self.filename!r}>"


class User(UserMixin, db.Model):
    """
    Адміністратор магазину.

    Використовується для входу в адмін-панель через Flask-Login.
    Пароль зберігається у вигляді хешу (werkzeug.security).
    """

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)     # False = обліковий запис заблоковано

    def __repr__(self):
        return f"<User id={self.id} email={self.email!r}>"


class ColorPalette(db.Model):
    """
    Глобальна палітра кольорів магазину.

    Служить джерелом при додаванні кольорів до товарів,
    щоб адміністратор не вводив HEX вручну щоразу.
    """

    id = db.Column(db.Integer, primary_key=True)
    color_name = db.Column(db.String(64), nullable=False)
    color_hex = db.Column(db.String(7), nullable=False)
    is_default = db.Column(db.Boolean, default=False)   # Чи є кольором за замовчуванням при виборі
    price_modifier = db.Column(db.Integer, default=0)
    sort_order = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f"<ColorPalette id={self.id} name={self.color_name!r}>"

    def to_dict(self):
        """Серіалізація для AJAX / JSON-відповідей."""
        return {
            "id": self.id,
            "color_name": self.color_name,
            "color_hex": self.color_hex,
            "is_default": self.is_default,
            "price_modifier": self.price_modifier,
        }


class TelegramUser(db.Model):
    """
    Прив'язка номера телефону покупця до Telegram chat_id.

    Використовується для надсилання сповіщень про статус замовлення
    безпосередньо в Telegram покупця.
    """

    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(20), unique=True, nullable=False)       # Телефон у форматі +380...
    chat_id = db.Column(db.BigInteger, unique=True, nullable=False)     # Telegram chat_id
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<TelegramUser id={self.id} phone={self.phone!r}>"