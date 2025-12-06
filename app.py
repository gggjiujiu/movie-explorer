import os

from dotenv import load_dotenv
from flask import Flask, render_template

from routes.favorites import favorites_bp
from routes.account import account_bp
from routes.auth import auth_bp
from routes.movies import movies_bp
from tmdb import ExternalAPIError


load_dotenv()


def create_app():
    app = Flask(__name__)
    # Set Secret Key for Session
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev_secret_key")

    # Register Blueprint
    app.register_blueprint(favorites_bp)
    app.register_blueprint(account_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(movies_bp)

    # -----------------------------
    # TMDB API DOWN ERROR PAGE
    # -----------------------------
    @app.errorhandler(ExternalAPIError)
    def handle_tmdb_error(e):
        app.logger.error(f"TMDB API error: {e}")
        return render_template("tmdb_error.html"), 503

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="127.0.0.1", port=8000)
