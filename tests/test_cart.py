from services.cart import CartService


def test_add_product_to_cart_returns_updated_count(client, sample_data):
    response = client.post(
        "/cart/add",
        json={
            "product_id": sample_data["product_id"],
            "color_id": sample_data["color_id"],
            "quantity": 2,
        },
    )

    data = response.get_json()

    assert response.status_code == 200
    assert data["ok"] is True
    assert data["cart_count"] == 2


def test_add_composition_to_cart_returns_updated_count(client, sample_data):
    response = client.post(
        "/cart/add",
        json={
            "composition_id": sample_data["composition_id"],
            "quantity": 1,
        },
    )

    data = response.get_json()

    assert response.status_code == 200
    assert data["ok"] is True
    assert data["cart_count"] == 1


def test_update_cart_item_quantity(client, sample_data):
    with client.session_transaction() as session:
        session[CartService.KEY] = [
            {
                "product_id": sample_data["product_id"],
                "color_id": sample_data["color_id"],
                "quantity": 1,
                "unit_price": 275,
            }
        ]

    response = client.post("/cart/update/0", json={"quantity": 3})

    assert response.status_code == 200
    assert response.get_json()["ok"] is True

    with client.session_transaction() as session:
        assert session[CartService.KEY][0]["quantity"] == 3


def test_remove_cart_item(client, sample_data):
    with client.session_transaction() as session:
        session[CartService.KEY] = [
            {
                "composition_id": sample_data["composition_id"],
                "quantity": 1,
                "unit_price": 700,
            }
        ]

    response = client.post("/cart/remove/0")

    assert response.status_code == 200
    assert response.get_json()["ok"] is True

    with client.session_transaction() as session:
        assert session.get(CartService.KEY) == []
