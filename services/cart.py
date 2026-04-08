# services/cart.py
# Сесійний кошик покупця.
# Дані зберігаються у Flask-сесії (підписаний cookie) — серверна БД не потрібна.
# Кошик — список словників двох типів:
#   {"product_id": int, "color_id": int|None, "quantity": int, "unit_price": int}
#   {"composition_id": int, "quantity": int, "unit_price": int}

from flask import session


class CartService:
    KEY = "cart"  # ключ у Flask-сесії

    @classmethod
    def get(cls) -> list:
        """Повертає поточний вміст кошика (порожній список якщо кошик відсутній)."""
        return session.get(cls.KEY, [])

    @classmethod
    def set(cls, cart: list) -> None:
        """Зберігає кошик у сесію та позначає сесію як змінену."""
        session[cls.KEY] = cart
        session.modified = True  # явно сигналізуємо Flask про зміну

    @classmethod
    def add_product(cls, product_id: int, color_id: int | None, quantity: int, unit_price: int) -> None:
        """
        Додає товар до кошика.
        Якщо товар з таким самим product_id + color_id вже є — збільшує кількість.
        """
        cart = cls.get()
        for item in cart:
            if item.get("product_id") == product_id and item.get("color_id") == color_id:
                item["quantity"] += quantity
                cls.set(cart)
                return
        cart.append({
            "product_id": product_id,
            "color_id": color_id,
            "quantity": quantity,
            "unit_price": unit_price,
        })
        cls.set(cart)

    @classmethod
    def add_composition(cls, composition_id: int, quantity: int, unit_price: int) -> None:
        """
        Додає композицію до кошика.
        Якщо та сама composition_id вже є — збільшує кількість.
        """
        cart = cls.get()
        for item in cart:
            if item.get("composition_id") == composition_id:
                item["quantity"] += quantity
                cls.set(cart)
                return
        cart.append({
            "composition_id": composition_id,
            "quantity": quantity,
            "unit_price": unit_price,
        })
        cls.set(cart)

    @classmethod
    def update_quantity(cls, index: int, quantity: int) -> None:
        """
        Оновлює кількість позиції за індексом.
        Мінімальна кількість — 1 (не дозволяємо обнулити через цей метод).
        """
        cart = cls.get()
        if 0 <= index < len(cart):
            cart[index]["quantity"] = max(1, int(quantity))
            cls.set(cart)

    @classmethod
    def remove(cls, index: int) -> None:
        """Видаляє позицію з кошика за індексом."""
        cart = cls.get()
        if 0 <= index < len(cart):
            cart.pop(index)
            cls.set(cart)

    @classmethod
    def clear(cls) -> None:
        """Очищає кошик (викликається після успішного оформлення замовлення)."""
        cls.set([])

    @classmethod
    def count(cls) -> int:
        """Повертає загальну кількість одиниць товарів у кошику (для бейджа в навбарі)."""
        return sum(item.get("quantity", 0) for item in cls.get())