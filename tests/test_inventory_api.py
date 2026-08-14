import pytest

from inventory_app import create_app


@pytest.fixture
def client():
    app = create_app(test_config={"TESTING": True})
    with app.test_client() as client:
        yield client


def test_get_inventory_returns_list(client):
    response = client.get("/inventory")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_post_inventory_creates_new_item(client):
    payload = {
        "name": "Bananas",
        "quantity": 12,
        "price": 2.5,
        "category": "Fruit",
        "barcode": "1234567890123",
    }

    response = client.post("/inventory", json=payload)
    assert response.status_code == 201
    data = response.get_json()
    assert data["name"] == "Bananas"
    assert data["quantity"] == 12
    assert data["barcode"] == "1234567890123"


def test_patch_inventory_updates_item(client):
    response = client.post(
        "/inventory",
        json={
            "name": "Apples",
            "quantity": 5,
            "price": 3.0,
            "category": "Fruit",
            "barcode": "9876543210123",
        },
    )
    item_id = response.get_json()["id"]

    update_response = client.patch(
        f"/inventory/{item_id}",
        json={"quantity": 9, "price": 3.75},
    )

    assert update_response.status_code == 200
    updated = update_response.get_json()
    assert updated["quantity"] == 9
    assert updated["price"] == 3.75


def test_delete_inventory_removes_item(client):
    response = client.post(
        "/inventory",
        json={
            "name": "Oranges",
            "quantity": 7,
            "price": 2.25,
            "category": "Fruit",
            "barcode": "1111222233334",
        },
    )
    item_id = response.get_json()["id"]

    delete_response = client.delete(f"/inventory/{item_id}")
    assert delete_response.status_code == 200
    assert delete_response.get_json()["message"] == "Item deleted successfully"

    get_response = client.get(f"/inventory/{item_id}")
    assert get_response.status_code == 404


def test_product_search_feature_uses_remote_lookup(client, monkeypatch):
    class FakeResponse:
        def __init__(self):
            self.status_code = 200

        def json(self):
            return {
                "status": 1,
                "product": {
                    "product_name": "Milk",
                    "brands": "Local Dairy",
                    "categories": "Dairy",
                    "ingredients_text": "Milk",
                },
            }

    monkeypatch.setattr(
        "inventory_app.routes.requests.get",
        lambda *args, **kwargs: FakeResponse(),
    )

    response = client.get("/products/search?query=milk")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["product_name"] == "Milk"
    assert payload["brands"] == "Local Dairy"
