import argparse
import requests

BASE_URL = "http://127.0.0.1:5000"


def list_items():
    response = requests.get(f"{BASE_URL}/inventory")
    response.raise_for_status()
    items = response.json()
    for item in items:
        print(f"{item['id']} | {item['name']} | qty={item['quantity']} | price=${item['price']}")


def add_item(args):
    payload = {
        "name": args.name,
        "quantity": args.quantity,
        "price": args.price,
        "category": args.category,
        "barcode": args.barcode,
    }
    response = requests.post(f"{BASE_URL}/inventory", json=payload)
    print(response.json())


def update_item(args):
    payload = {}
    if args.name is not None:
        payload["name"] = args.name
    if args.quantity is not None:
        payload["quantity"] = args.quantity
    if args.price is not None:
        payload["price"] = args.price
    if args.category is not None:
        payload["category"] = args.category
    if args.barcode is not None:
        payload["barcode"] = args.barcode

    response = requests.patch(f"{BASE_URL}/inventory/{args.id}", json=payload)
    print(response.json())


def delete_item(args):
    response = requests.delete(f"{BASE_URL}/inventory/{args.id}")
    print(response.json())


def search_product(args):
    params = {}
    if args.query:
        params["query"] = args.query
    if args.barcode:
        params["barcode"] = args.barcode
    response = requests.get(f"{BASE_URL}/products/search", params=params)
    print(response.json())


def build_parser():
    parser = argparse.ArgumentParser(description="Inventory management CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="List all inventory items")

    add_parser = subparsers.add_parser("add", help="Add a new inventory item")
    add_parser.add_argument("name")
    add_parser.add_argument("quantity", type=int)
    add_parser.add_argument("price", type=float)
    add_parser.add_argument("category")
    add_parser.add_argument("--barcode")
    add_parser.set_defaults(func=add_item)

    update_parser = subparsers.add_parser("update", help="Update inventory item")
    update_parser.add_argument("id", type=int)
    update_parser.add_argument("--name")
    update_parser.add_argument("--quantity", type=int)
    update_parser.add_argument("--price", type=float)
    update_parser.add_argument("--category")
    update_parser.add_argument("--barcode")
    update_parser.set_defaults(func=update_item)

    delete_parser = subparsers.add_parser("delete", help="Delete inventory item")
    delete_parser.add_argument("id", type=int)
    delete_parser.set_defaults(func=delete_item)

    search_parser = subparsers.add_parser("search", help="Look up product details")
    search_parser.add_argument("--query")
    search_parser.add_argument("--barcode")
    search_parser.set_defaults(func=search_product)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "list":
        list_items()
    else:
        args.func(args)


if __name__ == "__main__":
    main()
