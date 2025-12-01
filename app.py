import os
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, request, abort

from db import is_favorite
from tmdb import TMDB_API_KEY, get_movie_details, search_movies
from routes.favorites import favorites_bp
from routes.account import account_bp



def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv("SECRET_KEY")

    # Register Blueprint
    app.register_blueprint(favorites_bp)
    app.register_blueprint(account_bp)

    # 1. Login
    @app.route("/", methods=["GET"])
    def home():
        return render_template("home.html")

    # 2. movies
    @app.route("/movies", methods=["GET"])
    def movie_search():
        if not TMDB_API_KEY:
            abort(500, "TMDB_API_KEY is not set. Please configure it in your environment.")

        q = request.args.get("q", "").strip()
        year = request.args.get("year", "").strip()

        movies = []
        if q:
            movies = search_movies(q, year or None)

        return render_template(
            "movies_search.html",
            q=q,
            year=year,
            movies=movies,
        )

    # 3. movie detail 
    @app.route("/movies/<int:movie_id>", methods=["GET"])
    def movie_detail(movie_id: int):
        if not TMDB_API_KEY:
            abort(500, "TMDB_API_KEY is not set. Please configure it in your environment.")

        user_id = 8
        movie = get_movie_details(movie_id)
        fav_status = is_favorite(user_id, movie_id)

        return render_template("movie_detail.html", movie=movie, is_fav=fav_status)

    return app


if __name__ == "__main__":
    app = create_app()
    
    app.run(debug=True, host="127.0.0.1", port=8080)
