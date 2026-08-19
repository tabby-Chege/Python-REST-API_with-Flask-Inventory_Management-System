# Python REST API with Flask - Inventory Management System

## Project Description

This project is a Flask-based REST API for managing an inventory system.

The application allows users to create, view, update, delete, and search inventory products through API endpoints. It also integrates with the OpenFoodFacts API to retrieve product information using a barcode or product name.

The project demonstrates the use of Python, Flask, RESTful API design, external API integration, testing, command-line tools, and Git/GitHub.

## Features

- Create inventory products
- Retrieve all products
- Retrieve a single product
- Update product information
- Delete products
- Search products by name
- Search products by barcode
- Integrate with the OpenFoodFacts API
- Command-line interface (CLI)
- Automated testing with pytest
- Local data persistence
- Input validation and error handling

## Technologies Used

- Python 3
- Flask
- Requests
- Pytest
- OpenFoodFacts API
- Git
- GitHub

## Project Structure

```text
Python-REST-API_with-Flask-Inventory_Management-System/
│
├── inventory_app/
│   ├── __init__.py
│   ├── cli.py
│   └── routes.py
│
├── tests/
│   └── test_inventory_api.py
│
├── .gitignore
├── PROJECT_VERIFICATION.md
├── README.md
├── requirements.txt
└── run.py
