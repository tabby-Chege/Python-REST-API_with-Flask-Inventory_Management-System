import pytest

from inventory_app import create_app


@pytest.fixture
def client():
    app = create_app(test_config={"TESTING": True})
    with app.test_client() as client:
        yield client


class TestIndexAndHealthCheck:
    """Test suite for API health check and index endpoint"""

    def test_index_returns_running_message(self, client):
        """Test that index endpoint returns API running status"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.get_json()
        assert "message" in data
        assert "running" in data["message"].lower()


class TestInventoryRead:
    """Test suite for reading inventory items"""

    def test_get_inventory_returns_list(self, client):
        """Test retrieving all inventory items returns a list"""
        response = client.get("/inventory")
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_get_single_inventory_item(self, client):
        """Test retrieving a single inventory item by ID"""
        # First get the inventory to find an existing item
        response = client.get("/inventory")
        items = response.get_json()
        item_id = items[0]["id"]

        # Now get the single item
        response = client.get(f"/inventory/{item_id}")
        assert response.status_code == 200
        data = response.get_json()
        assert data["id"] == item_id
        assert "name" in data
        assert "quantity" in data
        assert "price" in data

    def test_get_nonexistent_item_returns_404(self, client):
        """Test that getting a non-existent item returns 404"""
        response = client.get("/inventory/99999")
        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data


class TestInventoryCreate:
    """Test suite for creating inventory items"""

    def test_post_inventory_creates_new_item(self, client):
        """Test creating a new inventory item"""
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
        assert "id" in data

    def test_post_inventory_with_product_details(self, client, monkeypatch):
        """Test creating item and enriching with external product details"""
        class FakeResponse:
            status_code = 200
            def json(self):
                return {
                    "product": {
                        "product_name": "Organic Milk",
                        "brands": "Fresh Farm",
                        "categories": "Dairy",
                        "ingredients_text": "Milk",
                    }
                }

        monkeypatch.setattr(
            "inventory_app.routes.requests.get",
            lambda *args, **kwargs: FakeResponse(),
        )

        payload = {
            "name": "Milk",
            "quantity": 10,
            "price": 3.99,
            "category": "Dairy",
            "barcode": "5555666677778",
        }

        response = client.post("/inventory", json=payload)
        assert response.status_code == 201
        data = response.get_json()
        assert "product_details" in data
        assert data["product_details"]["product_name"] == "Organic Milk"

    def test_post_inventory_missing_required_field_name(self, client):
        """Test creating item without required 'name' field"""
        payload = {
            "quantity": 12,
            "price": 2.5,
            "category": "Fruit",
        }

        response = client.post("/inventory", json=payload)
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "name" in data["error"]

    def test_post_inventory_missing_required_field_quantity(self, client):
        """Test creating item without required 'quantity' field"""
        payload = {
            "name": "Bananas",
            "price": 2.5,
            "category": "Fruit",
        }

        response = client.post("/inventory", json=payload)
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "quantity" in data["error"]

    def test_post_inventory_missing_required_field_price(self, client):
        """Test creating item without required 'price' field"""
        payload = {
            "name": "Bananas",
            "quantity": 12,
            "category": "Fruit",
        }

        response = client.post("/inventory", json=payload)
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "price" in data["error"]

    def test_post_inventory_missing_required_field_category(self, client):
        """Test creating item without required 'category' field"""
        payload = {
            "name": "Bananas",
            "quantity": 12,
            "price": 2.5,
        }

        response = client.post("/inventory", json=payload)
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "category" in data["error"]

    def test_post_inventory_with_empty_payload(self, client):
        """Test creating item with empty payload"""
        response = client.post("/inventory", json={})
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_post_inventory_with_zero_quantity(self, client):
        """Test creating item with zero quantity"""
        payload = {
            "name": "Test Item",
            "quantity": 0,
            "price": 1.99,
            "category": "Test",
        }

        response = client.post("/inventory", json=payload)
        assert response.status_code == 201
        data = response.get_json()
        assert data["quantity"] == 0

    def test_post_inventory_with_large_quantity(self, client):
        """Test creating item with large quantity"""
        payload = {
            "name": "Test Item",
            "quantity": 999999,
            "price": 1.99,
            "category": "Test",
        }

        response = client.post("/inventory", json=payload)
        assert response.status_code == 201
        data = response.get_json()
        assert data["quantity"] == 999999


class TestInventoryUpdate:
    """Test suite for updating inventory items"""

    def test_patch_inventory_updates_item(self, client):
        """Test updating an existing inventory item"""
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
        # Ensure other fields remain unchanged
        assert updated["name"] == "Apples"

    def test_patch_inventory_updates_name(self, client):
        """Test updating only the name field"""
        response = client.post(
            "/inventory",
            json={
                "name": "Original Name",
                "quantity": 5,
                "price": 3.0,
                "category": "Fruit",
            },
        )
        item_id = response.get_json()["id"]

        update_response = client.patch(
            f"/inventory/{item_id}",
            json={"name": "Updated Name"},
        )

        assert update_response.status_code == 200
        updated = update_response.get_json()
        assert updated["name"] == "Updated Name"
        assert updated["quantity"] == 5  # Should remain unchanged

    def test_patch_nonexistent_item_returns_404(self, client):
        """Test updating a non-existent item returns 404"""
        response = client.patch(
            "/inventory/99999",
            json={"quantity": 10},
        )
        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data

    def test_patch_inventory_with_no_data_returns_400(self, client):
        """Test patching with empty payload returns error"""
        response = client.post(
            "/inventory",
            json={
                "name": "Test",
                "quantity": 5,
                "price": 3.0,
                "category": "Test",
            },
        )
        item_id = response.get_json()["id"]

        update_response = client.patch(
            f"/inventory/{item_id}",
            json={},
        )
        assert update_response.status_code == 400

    def test_patch_inventory_with_barcode_updates_product_details(self, client, monkeypatch):
        """Test updating barcode fetches new product details"""
        class FakeResponse:
            status_code = 200
            def json(self):
                return {
                    "product": {
                        "product_name": "Premium Milk",
                        "brands": "Luxury Dairy",
                        "categories": "Dairy",
                        "ingredients_text": "Milk",
                    }
                }

        monkeypatch.setattr(
            "inventory_app.routes.requests.get",
            lambda *args, **kwargs: FakeResponse(),
        )

        response = client.post(
            "/inventory",
            json={
                "name": "Milk",
                "quantity": 5,
                "price": 3.0,
                "category": "Dairy",
            },
        )
        item_id = response.get_json()["id"]

        update_response = client.patch(
            f"/inventory/{item_id}",
            json={"barcode": "1111222233334"},
        )

        assert update_response.status_code == 200
        updated = update_response.get_json()
        assert "product_details" in updated


class TestInventoryDelete:
    """Test suite for deleting inventory items"""

    def test_delete_inventory_removes_item(self, client):
        """Test deleting an inventory item"""
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

    def test_delete_nonexistent_item_returns_404(self, client):
        """Test deleting a non-existent item returns 404"""
        response = client.delete("/inventory/99999")
        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data


class TestExternalAPIIntegration:
    """Test suite for external API integration"""

    def test_product_search_feature_uses_remote_lookup(self, client, monkeypatch):
        """Test searching for product details from external API"""
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

    def test_product_search_with_barcode(self, client, monkeypatch):
        """Test searching for product by barcode"""
        class FakeResponse:
            def __init__(self):
                self.status_code = 200

            def json(self):
                return {
                    "product": {
                        "product_name": "Cheese",
                        "brands": "Dairy Co",
                        "categories": "Cheese",
                        "ingredients_text": "Cheese",
                        "code": "1234567890123",
                    },
                }

        monkeypatch.setattr(
            "inventory_app.routes.requests.get",
            lambda *args, **kwargs: FakeResponse(),
        )

        response = client.get("/products/search?barcode=1234567890123")
        assert response.status_code == 200
        payload = response.get_json()
        assert payload["product_name"] == "Cheese"
        assert payload["barcode"] == "1234567890123"

    def test_product_search_missing_parameters_returns_400(self, client):
        """Test searching without query or barcode returns error"""
        response = client.get("/products/search")
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_product_search_not_found_returns_404(self, client, monkeypatch):
        """Test searching for non-existent product returns 404"""
        class FakeResponse:
            def __init__(self):
                self.status_code = 200

            def json(self):
                return {"status": 0, "products": []}

        monkeypatch.setattr(
            "inventory_app.routes.requests.get",
            lambda *args, **kwargs: FakeResponse(),
        )

        response = client.get("/products/search?query=nonexistent")
        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data

    def test_product_search_api_timeout_returns_404(self, client, monkeypatch):
        """Test handling of API timeout"""
        import requests
        
        def mock_get(*args, **kwargs):
            raise requests.RequestException("Timeout")

        monkeypatch.setattr(
            "inventory_app.routes.requests.get",
            mock_get,
        )

        response = client.get("/products/search?query=milk")
        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data
