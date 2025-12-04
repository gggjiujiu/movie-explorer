import os
from dotenv import load_dotenv
load_dotenv()

from flask import Flask

from routes.favorites import favorites_bp
from routes.account import account_bp
from routes.auth import auth_bp
from routes.movies import movies_bp


def create_app():
    app = Flask(__name__)
    # Set Secret Key for Session
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev_secret_key")

    # Register Blueprint
    app.register_blueprint(favorites_bp)
    app.register_blueprint(account_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(movies_bp)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="127.0.0.1", port=8000)
