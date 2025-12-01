import os

# ---------- Iris ----------
from dotenv import load_dotenv
# -------------------------

from flask import Flask, render_template, request, abort
import requests

# ---------- Iris ----------
from routes_account import account_bp

load_dotenv()
# -------------------------

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMG_BASE = "https://image.tmdb.org/t/p/w342"  # poster image size


def create_app():
    app = Flask(__name__)

    # ---------- Iris ----------
    app.secret_key = "my_super_secret_key_for_group_project_movie"
    app.register_blueprint(account_bp)
    # -------------------------

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

        movie = get_movie_details(movie_id)
        return render_template("movie_detail.html", movie=movie)

    ''' ---------- Iris Delete ----------
    # 4. user account
    @app.route("/account", methods=["GET"])
    def account():
        return render_template("account.html")
    ''' 

    # 5. favourites list
    @app.route("/favourites", methods=["GET"])
    def favourites():
        return render_template("favourites.html")

    return app


def search_movies(query: str, year: str | None = None):
    """Call TMDb search API and return a simplified list of movies."""
    params = {
        "api_key": TMDB_API_KEY,
        "query": query,
        "include_adult": False,
        "language": "en-US",
    }
    if year:
        params["year"] = year

    resp = requests.get(f"{TMDB_BASE_URL}/search/movie", params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    movies: list[dict] = []
    for m in data.get("results", []):
        movies.append({
            "id": m["id"],
            "title": m["title"],
            "rating": m.get("vote_average"),
            "vote_count": m.get("vote_count"),
            "poster_url": TMDB_IMG_BASE + m["poster_path"] if m.get("poster_path") else None,
            "overview": m.get("overview"),
            "release_year": (m.get("release_date") or "")[:4],
        })
    return movies


def get_movie_details(movie_id: int):
    """Get detailed information for a single movie by id."""
    params = {
        "api_key": TMDB_API_KEY,
        "language": "en-US",
    }
    resp = requests.get(f"{TMDB_BASE_URL}/movie/{movie_id}", params=params, timeout=10)
    resp.raise_for_status()
    m = resp.json()

    return {
        "id": m["id"],
        "title": m["title"],
        "rating": m.get("vote_average"),
        "vote_count": m.get("vote_count"),
        "poster_url": TMDB_IMG_BASE + m["poster_path"] if m.get("poster_path") else None,
        "overview": m.get("overview"),
        "release_year": (m.get("release_date") or "")[:4],
        "genres": [g["name"] for g in m.get("genres", [])],
        "runtime": m.get("runtime"),
    }


if __name__ == "__main__":
    app = create_app()
    
    app.run(debug=True, host="127.0.0.1", port=8080)
