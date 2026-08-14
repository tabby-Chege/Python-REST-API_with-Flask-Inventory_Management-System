from flask import Flask
from .routes import register_routes


def create_app(test_config=None):
    app = Flask(__name__)
    app.config["JSON_SORT_KEYS"] = False

    if test_config:
        app.config.update(test_config)

    register_routes(app)
    return app
