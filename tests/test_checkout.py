import blueprints.shop.routes as shop_routes

from models import Order, OrderItem
from services.cart import CartService


def test_checkout_redirects_to_cart_when_cart_is_empty(client):
    with client.session_transaction() as session:
        session["phone_verified"] = "+380991112233"

    response = client.post(
        "/checkout",
        data={
            "name": "Іван",
            "phone": "+380991112233",
            "contact_method": "phone",
            "delivery_type": "pickup",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/cart")


def test_checkout_creates_order_from_product_cart(client, app, sample_data, monkeypatch):
    monkeypatch.setattr(shop_routes, "send_order_notification", lambda order: None)

    with client.session_transaction() as session:
        session["phone_verified"] = "+380991112233"
        session[CartService.KEY] = [
            {
                "product_id": sample_data["product_id"],
                "color_id": sample_data["color_id"],
                "quantity": 2,
                "unit_price": 275,
            }
        ]

    response = client.post(
        "/checkout",
        data={
            "name": "Іван",
            "phone": "+380991112233",
            "contact_method": "phone",
            "delivery_type": "pickup",
            "comment": "Тестове замовлення",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert "/order/success/" in response.headers["Location"]

    with app.app_context():
        order = Order.query.one()
        item = OrderItem.query.one()

        assert order.customer_name == "Іван"
        assert order.delivery_type == "pickup"
        assert order.total_amount == 550
        assert order.order_number is not None
        assert item.product_id == sample_data["product_id"]
        assert item.quantity == 2
        assert item.unit_price == 275

    with client.session_transaction() as session:
        assert session.get(CartService.KEY) == []


def test_checkout_creates_order_from_composition_cart(client, app, sample_data, monkeypatch):
    monkeypatch.setattr(shop_routes, "send_order_notification", lambda order: None)

    with client.session_transaction() as session:
        session["phone_verified"] = "+380991112244"
        session[CartService.KEY] = [
            {
                "composition_id": sample_data["composition_id"],
                "quantity": 1,
                "unit_price": 700,
            }
        ]

    response = client.post(
        "/checkout",
        data={
            "name": "Олена",
            "phone": "+380991112244",
            "contact_method": "viber",
            "delivery_type": "nova_poshta",
            "np_city_name": "Київ",
            "np_warehouse": "Відділення 1",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert "/order/success/" in response.headers["Location"]

    with app.app_context():
        order = Order.query.one()
        item = OrderItem.query.one()

        assert order.customer_name == "Олена"
        assert order.delivery_type == "nova_poshta"
        assert order.np_city_name == "Київ"
        assert order.np_warehouse == "Відділення 1"
        assert order.total_amount == 700
        assert item.composition_id == sample_data["composition_id"]
        assert item.quantity == 1
