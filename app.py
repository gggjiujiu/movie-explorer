import os
from flask import Flask
from dotenv import load_dotenv
from db import db

from routes.auth import auth_bp
from routes.movies import movies_bp

load_dotenv()


def create_app():
    app = Flask(__name__)
    # Set Secret Key for Session
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev_secret_key")

    # Database set up
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "sqlite:///local_dev.db")
    if (app.config['SQLALCHEMY_DATABASE_URI'] and
            app.config['SQLALCHEMY_DATABASE_URI'].startswith("postgres://")):
        app.config['SQLALCHEMY_DATABASE_URI'] = (
            app.config['SQLALCHEMY_DATABASE_URI'].replace(
                "postgres://", "postgresql://", 1
            )
        )

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initiate database
    db.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(movies_bp)

    # Automatically create tables (if they don't exist)
    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="127.0.0.1", port=8000)
