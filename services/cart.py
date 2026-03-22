# services/cart.py
from flask import session

class CartService:
    KEY = "cart"

    @classmethod
    def get(cls):
        return session.get(cls.KEY, [])

    @classmethod
    def set(cls, cart):
        session[cls.KEY] = cart

    @classmethod
    def add_product(cls, product_id, color_id, quantity, unit_price):
        cart = cls.get()
        for item in cart:
            if item.get("product_id") == product_id and item.get("color_id") == color_id:
                item["quantity"] += quantity
                break
        else:
            cart.append({
                "product_id": product_id,
                "color_id": color_id,
                "quantity": quantity,
                "unit_price": unit_price
            })
        cls.set(cart)

    @classmethod
    def add_composition(cls, composition_id, quantity, unit_price):
        cart = cls.get()
        for item in cart:
            if item.get("composition_id") == composition_id:
                item["quantity"] += quantity
                break
        else:
            cart.append({
                "composition_id": composition_id,
                "quantity": quantity,
                "unit_price": unit_price
            })
        cls.set(cart)

    @classmethod
    def update_quantity(cls, index, quantity):
        cart = cls.get()
        if 0 <= index < len(cart):
            cart[index]["quantity"] = max(1, int(quantity))
            cls.set(cart)

    @classmethod
    def remove(cls, index):
        cart = cls.get()
        if 0 <= index < len(cart):
            cart.pop(index)
            cls.set(cart)

    @classmethod
    def clear(cls):
        cls.set([])