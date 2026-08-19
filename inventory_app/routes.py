from flask import jsonify, request
import requests

inventory = [
    {
        "id": 1,
        "name": "Organic Almond Milk",
        "quantity": 24,
        "price": 4.50,
        "category": "Dairy Alternatives",
        "barcode": "1234567890123",
        "product_details": {
            "product_name": "Organic Almond Milk",
            "brands": "Silk",
            "categories": "Plant-based milk",
            "ingredients_text": "Filtered water, almonds, cane sugar, sunflower lecithin",
        },
    },
    {
        "id": 2,
        "name": "Whole Wheat Bread",
        "quantity": 18,
        "price": 3.75,
        "category": "Bakery",
        "barcode": "9876543210987",
        "product_details": {
            "product_name": "Whole Wheat Bread",
            "brands": "Best Bake",
            "categories": "Breads",
            "ingredients_text": "Whole wheat flour, water, yeast, salt",
        },
    },
]


def _next_id():
    return max((item["id"] for item in inventory), default=0) + 1


def _normalize_product(product):
    return {
        "product_name": product.get("product_name") or product.get("name") or "Unknown product",
        "brands": product.get("brands"),
        "categories": product.get("categories"),
        "ingredients_text": product.get("ingredients_text"),
        "barcode": product.get("code") or product.get("barcode"),
    }


def fetch_product_details(barcode=None, name=None):
    headers = {
        "User-Agent": "InventoryManagementSystem/1.0 (Python requests)"
    }

    if barcode:
        try:
            response = requests.get(
                f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json",
                headers=headers,
                timeout=10,
            )
        except requests.RequestException:
            response = None

        if response and getattr(response, "status_code", 200) == 200:
            payload = response.json() or {}
            product = payload.get("product") or payload

            if isinstance(product, dict) and (
                product.get("product_name")
                or product.get("name")
                or product.get("brands")
            ):
                return _normalize_product(product)

    if name:
        try:
            response = requests.get(
                "https://world.openfoodfacts.org/cgi/search.pl",
                params={
                    "search_terms": name,
                    "search_simple": 1,
                    "action": "process",
                    "json": 1,
                    "page_size": 1,
                },
                headers=headers,
                timeout=10,
            )
        except requests.RequestException:
            response = None

        if response and getattr(response, "status_code", 200) == 200:
            payload = response.json() or {}
            candidates = []

            direct_product = payload.get("product")
            if isinstance(direct_product, dict):
                candidates.append(direct_product)

            products = payload.get("products") or []
            if isinstance(products, list):
                candidates.extend(products)

            if not candidates and isinstance(payload, dict) and (
                payload.get("product_name")
                or payload.get("name")
                or payload.get("brands")
            ):
                candidates.append(payload)

            for candidate in candidates:
                if isinstance(candidate, dict) and (
                    candidate.get("product_name")
                    or candidate.get("name")
                    or candidate.get("brands")
                ):
                    return _normalize_product(candidate)

    return None


def register_routes(app):
    @app.route("/")
    def index():
        return jsonify({"message": "Inventory management API is running."})

    @app.route("/inventory", methods=["GET"])
    def get_inventory():
        return jsonify(inventory)

    @app.route("/inventory/<int:item_id>", methods=["GET"])
    def get_inventory_item(item_id):
        item = next((entry for entry in inventory if entry["id"] == item_id), None)
        if item is None:
            return jsonify({"error": "Item not found"}), 404
        return jsonify(item)

    @app.route("/inventory", methods=["POST"])
    def create_inventory_item():
        payload = request.get_json(silent=True) or {}

        required_fields = ["name", "quantity", "price", "category"]
        missing = [field for field in required_fields if field not in payload]
        if missing:
            return jsonify({"error": f"Missing required field(s): {', '.join(missing)}"}), 400

        item = {
            "id": _next_id(),
            "name": payload["name"],
            "quantity": int(payload["quantity"]),
            "price": float(payload["price"]),
            "category": payload["category"],
            "barcode": payload.get("barcode"),
        }

        product_details = fetch_product_details(item.get("barcode"), item.get("name"))
        if product_details:
            item["product_details"] = product_details

        inventory.append(item)
        return jsonify(item), 201

    @app.route("/inventory/<int:item_id>", methods=["PATCH"])
    def update_inventory_item(item_id):
        item = next((entry for entry in inventory if entry["id"] == item_id), None)
        if item is None:
            return jsonify({"error": "Item not found"}), 404

        payload = request.get_json(silent=True) or {}
        if not payload:
            return jsonify({"error": "No update data provided"}), 400

        for key in ["name", "quantity", "price", "category", "barcode"]:
            if key in payload:
                if key == "quantity":
                    item[key] = int(payload[key])
                elif key == "price":
                    item[key] = float(payload[key])
                else:
                    item[key] = payload[key]

        if "barcode" in payload or "name" in payload:
            item["product_details"] = fetch_product_details(
                item.get("barcode"),
                item.get("name"),
            ) or item.get("product_details")

        return jsonify(item)

    @app.route("/inventory/<int:item_id>", methods=["DELETE"])
    def delete_inventory_item(item_id):
        for index, item in enumerate(inventory):
            if item["id"] == item_id:
                del inventory[index]
                return jsonify({"message": "Item deleted successfully"})
        return jsonify({"error": "Item not found"}), 404

    @app.route("/products/search", methods=["GET"])
    def search_product():
        query = request.args.get("query", "").strip()
        barcode = request.args.get("barcode", "").strip()

        if not query and not barcode:
            return jsonify({"error": "Provide a product name or barcode"}), 400

        product = fetch_product_details(barcode=barcode or None, name=query or None)
        if product is None:
            return jsonify({"error": "No product found"}), 404

        return jsonify(product)
