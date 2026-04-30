from models import ColorPalette, Composition, Product


def login_as_admin(client, email="admin@example.com", password="secret123"):
    return client.post(
        "/admin/login",
        data={"email": email, "password": password},
        follow_redirects=False,
    )


def test_admin_login_page_opens(client):
    response = client.get("/admin/login")

    assert response.status_code == 200
    assert "Вхід до адмінки" in response.get_data(as_text=True)


def test_admin_pages_redirect_to_login_for_anonymous_user(client):
    response = client.get("/admin/products", follow_redirects=False)

    assert response.status_code == 302
    assert "/admin/login" in response.headers["Location"]


def test_admin_can_login_with_valid_credentials(client, admin_user):
    response = login_as_admin(client)

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/admin/")


def test_admin_login_rejects_invalid_password(client, admin_user):
    response = login_as_admin(client, password="wrong-password")

    assert response.status_code == 200
    assert "Невірний логін або пароль" in response.get_data(as_text=True)


def test_admin_index_opens_after_login(client, admin_user):
    login_as_admin(client)

    response = client.get("/admin/")

    assert response.status_code == 200
    assert "Адмін-панель" in response.get_data(as_text=True)


def test_admin_product_list_opens_after_login(client, admin_user, sample_data):
    login_as_admin(client)

    response = client.get("/admin/products")

    assert response.status_code == 200
    assert "Товари" in response.get_data(as_text=True)
    assert "Тестова свічка" in response.get_data(as_text=True)


def test_admin_composition_list_opens_after_login(client, admin_user, sample_data):
    login_as_admin(client)

    response = client.get("/admin/compositions")

    assert response.status_code == 200
    assert "Композиції" in response.get_data(as_text=True)
    assert "Тестова композиція" in response.get_data(as_text=True)


def test_admin_order_list_opens_after_login(client, admin_user):
    login_as_admin(client)

    response = client.get("/admin/orders")

    assert response.status_code == 200
    assert "Замовлення" in response.get_data(as_text=True)


def test_admin_logout_clears_session(client, admin_user):
    login_as_admin(client)

    response = client.get("/admin/logout", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/admin/login")

    protected_response = client.get("/admin/", follow_redirects=False)
    assert protected_response.status_code == 302
    assert "/admin/login" in protected_response.headers["Location"]


def test_admin_product_create_form_opens_after_login(client, admin_user):
    login_as_admin(client)

    response = client.get("/admin/products/edit")

    assert response.status_code == 200
    assert "Створення товару" in response.get_data(as_text=True)


def test_admin_composition_create_form_opens_after_login(client, admin_user):
    login_as_admin(client)

    response = client.get("/admin/compositions/new")

    assert response.status_code == 200
    assert "Створення композиції" in response.get_data(as_text=True)


def test_admin_palette_page_opens_after_login(client, admin_user):
    login_as_admin(client)

    response = client.get("/admin/palette")

    assert response.status_code == 200
    assert "Палітра кольорів" in response.get_data(as_text=True)


def test_admin_can_add_palette_color(client, app, admin_user):
    login_as_admin(client)

    response = client.post(
        "/admin/palette/add",
        data={
            "color_name": "Червоний",
            "color_hex": "#ff0000",
            "price_modifier": "5",
            "sort_order": "1",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/admin/palette")

    with app.app_context():
        palette_color = ColorPalette.query.one()
        assert palette_color.color_name == "Червоний"
        assert palette_color.color_hex == "#ff0000"
        assert palette_color.price_modifier == 5


def test_admin_can_create_composition_without_image(client, app, admin_user):
    login_as_admin(client)

    response = client.post(
        "/admin/compositions/new",
        data={
            "title": "Нова композиція",
            "description": "Тестовий опис",
            "price": "900",
            "is_active": "on",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/admin/compositions")

    with app.app_context():
        composition = Composition.query.filter_by(title="Нова композиція").one()
        assert composition.description == "Тестовий опис"
        assert composition.price == 900
        assert composition.is_active is True


def test_admin_can_create_product_with_one_color(client, app, admin_user):
    login_as_admin(client)

    response = client.post(
        "/admin/products/edit",
        data={
            "sku": "1002",
            "name": "Нова тестова свічка",
            "description": "Створена в тесті",
            "price": "300",
            "wax_type": "Soy",
            "category": "Gift",
            "length": "10",
            "width": "20",
            "height": "30",
            "weight": "40",
            "color_id[]": "new",
            "color_name[]": "Синій",
            "color_hex[]": "#0000ff",
            "color_modifier_0": "15",
            "is_active": "on",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert "/admin/products/edit/" in response.headers["Location"]

    with app.app_context():
        product = Product.query.filter_by(sku="1002").one()
        assert product.name == "Нова тестова свічка"
        assert product.price == 300
        assert len(product.colors) == 1
        assert product.colors[0].color_name == "Синій"
        assert product.colors[0].price_modifier == 15
