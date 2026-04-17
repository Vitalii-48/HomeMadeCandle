def test_healthcheck_returns_ok(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_data(as_text=True) == "OK"


def test_home_page_opens(client, sample_data):
    response = client.get("/")

    assert response.status_code == 200


def test_catalog_page_opens(client, sample_data):
    response = client.get("/catalog")

    assert response.status_code == 200


def test_product_detail_page_opens(client, sample_data):
    response = client.get(f"/product/{sample_data['product_id']}")

    assert response.status_code == 200


def test_compositions_page_opens(client, sample_data):
    response = client.get("/compositions")

    assert response.status_code == 200
