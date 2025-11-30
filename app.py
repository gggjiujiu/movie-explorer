import os
import random
from flask import (
    Flask, render_template, request, abort, redirect, url_for, session, flash
)
from dotenv import load_dotenv
import requests
from models import db, User

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMG_BASE = "https://image.tmdb.org/t/p/w342"


def create_app():
    app = Flask(__name__)
    # Set Secret Key for Session
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev_secret_key")

    # Database set up
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
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

    # Automatically create tables (if they don't exist)
    with app.app_context():
        db.create_all()

    # --- Route Definitions ---

    # 1. Login / Home
    @app.route("/", methods=["GET"])
    def home():
        # If already logged in, redirect directly to the movie search page
        if 'user_id' in session:
            return redirect(url_for('movie_search'))
        return render_template("home.html")

    # Handle Registration (Sign Up)
    @app.route("/signup", methods=["POST"])
    def signup():
        firstname = request.form.get("firstname")
        lastname = request.form.get("lastname")
        email = request.form.get("email")
        password = request.form.get("password")

        # Check if the email is already registered
        if User.query.filter_by(email=email).first():
            return "Email already registered!", 400

        # Automatically generate account name (email prefix + random suffix)
        base_account = email.split('@')[0]
        random_suffix = str(random.randint(1000, 9999))
        generated_account = f"{base_account}_{random_suffix}"

        # Create new user instance
        new_user = User(
            firstname=firstname,
            lastname=lastname,
            email=email,
            account=generated_account
        )
        new_user.set_password(password)  # Encrypt the password

        db.session.add(new_user)
        db.session.commit()

        # Log in directly after successful registration
        session['user_id'] = new_user.id
        return redirect(url_for('movie_search'))

    # Handle Login
    @app.route("/login", methods=["POST"])
    def login():
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            return redirect(url_for('movie_search'))
        else:
            return "Invalid email or password", 401

    # Handle Logout
    @app.route("/logout")
    def logout():
        session.clear()
        flash("You have been logged out.")
        return redirect(url_for('home'))

    # 2. movies
    @app.route("/movies", methods=["GET"])
    def movie_search():
        if not TMDB_API_KEY:
            abort(500, "TMDB_API_KEY is not set.")

        q = request.args.get("q", "").strip()
        year = request.args.get("year", "").strip()
        genre_id = request.args.get("genre_id", "").strip()
        min_rating = request.args.get("min_rating", "").strip()

        genre_filter = int(genre_id) if genre_id else None
        rating_filter = float(min_rating) if min_rating else None

        movies = []  # search result
        recommended_movies = []  # recommend top 10 popular movies

        if q:
            # === Case A: User entered text search ===
            all_movies = search_movies(q, year or None)
            movies = apply_filters(all_movies, genre_filter, rating_filter)
        else:
            # === Case B: Homepage Browse / Pure Filtering ===
            recommended_movies = get_popular_movies(
                genre_id=genre_filter,
                min_rating=rating_filter,
                year=year
            )

        # genre dropdown list
        genres = get_movie_genres()

        return render_template(
            "movies_search.html",
            q=q,
            year=year,
            movies=movies,
            genres=genres,
            selected_genre=genre_id,
            selected_rating=min_rating,
            recommended_movies=recommended_movies,
        )

    # 3. Movie Detail
    @app.route("/movies/<int:movie_id>", methods=["GET"])
    def movie_detail(movie_id: int):
        if 'user_id' not in session:
            return redirect(url_for('home'))

        movie = get_movie_details(movie_id)
        return render_template("movie_detail.html", movie=movie)

    # 4. Account
    @app.route("/account", methods=["GET"])
    def account():
        if 'user_id' not in session:
            return redirect(url_for('home'))
        return render_template("account.html")

    # 5. Favourites
    @app.route("/favourites", methods=["GET"])
    def favourites():
        if 'user_id' not in session:
            return redirect(url_for('home'))
        return render_template("favourites.html")

    return app


# --- Helper Functions ---
def search_movies(query: str, year: str | None = None):
    params = {
        "api_key": TMDB_API_KEY,
        "query": query,
        "include_adult": False,
        "language": "en-US"
    }
    if year:
        params["year"] = year
    resp = requests.get(
        f"{TMDB_BASE_URL}/search/movie", params=params, timeout=10
    )
    resp.raise_for_status()
    data = resp.json()
    movies = []
    for m in data.get("results", []):
        poster_path = m.get("poster_path")
        poster_url = TMDB_IMG_BASE + poster_path if poster_path else None
        movies.append({
            "id": m["id"],
            "title": m["title"],
            "rating": m.get("vote_average"),
            "vote_count": m.get("vote_count"),
            "poster_url": poster_url,
            "overview": m.get("overview"),
            "release_year": (m.get("release_date") or "")[:4],
        })
    return movies


def get_popular_movies(genre_id=None, min_rating=None, year=None, limit=20):
    """
    Fetches popular movies using the /discover/movie endpoint.
    Supports filtering by genre, rating, and year directly via the API.
    Includes random pagination to ensure the homepage content varies.
    """
    if not TMDB_API_KEY:
        return []

    # Use the 'discover' endpoint instead of 'popular' to enable filtering
    endpoint = f"{TMDB_BASE_URL}/discover/movie"

    # To make the results random/fresh on every refresh,
    # we request a random page between 1 and 5.
    random_page = random.randint(1, 5)

    params = {
        "api_key": TMDB_API_KEY,
        "language": "en-US",
        "sort_by": "popularity.desc",  # Sort by popularity
        "include_adult": False,
        "include_video": False,
        "page": random_page,
    }

    # Add filter conditions to API request parameters
    if genre_id:
        params["with_genres"] = genre_id
    if min_rating:
        params["vote_average.gte"] = min_rating
    if year:
        params["primary_release_year"] = year

    resp = requests.get(endpoint, params=params, timeout=10)

    # Fallback: If the random page is out of range,
    # or if an error occurs, try fetching page 1.
    if resp.status_code != 200 or not resp.json().get("results"):
        params["page"] = 1
        resp = requests.get(endpoint, params=params, timeout=10)

    resp.raise_for_status()
    data = resp.json()

    movies = []
    for m in data.get("results", [])[:limit]:
        poster_path = m.get("poster_path")
        poster_url = TMDB_IMG_BASE + poster_path if poster_path else None
        movies.append({
            "id": m["id"],
            "title": m["title"],
            "rating": m.get("vote_average"),
            "vote_count": m.get("vote_count"),
            "poster_url": poster_url,
            "release_year": (m.get("release_date") or "")[:4],
            "genre_ids": m.get("genre_ids") or [],
        })
    return movies


def get_movie_details(movie_id: int):
    params = {"api_key": TMDB_API_KEY, "language": "en-US"}
    resp = requests.get(
        f"{TMDB_BASE_URL}/movie/{movie_id}", params=params, timeout=10
    )
    resp.raise_for_status()
    m = resp.json()
    poster_path = m.get("poster_path")
    return {
        "id": m["id"],
        "title": m["title"],
        "rating": m.get("vote_average"),
        "vote_count": m.get("vote_count"),
        "poster_url": TMDB_IMG_BASE + poster_path if poster_path else None,
        "overview": m.get("overview"),
        "release_year": (m.get("release_date") or "")[:4],
        "genres": [g["name"] for g in m.get("genres", [])],
        "runtime": m.get("runtime"),
    }


# to catch the genres list of TMDb for html
_genres_cache = None


def get_movie_genres():
    global _genres_cache
    if _genres_cache is not None:
        return _genres_cache

    if not TMDB_API_KEY:
        return []

    params = {
        "api_key": TMDB_API_KEY,
        "language": "en-US",
    }
    resp = requests.get(
        f"{TMDB_BASE_URL}/genre/movie/list", params=params, timeout=10
    )
    resp.raise_for_status()
    data = resp.json()
    _genres_cache = data.get("genres", [])
    return _genres_cache


def apply_filters(movie_list, genre_filter, rating_filter):
    filtered = []

    for m in movie_list:
        # Genre filter
        if genre_filter is not None:
            genre_ids = m.get("genre_ids", [])
            if genre_filter not in genre_ids:
                continue

        # Rating filter
        if rating_filter is not None:
            r = m.get("rating")
            if r is None:
                r = 0.0
            if r < rating_filter:
                continue

        filtered.append(m)

    return filtered


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="127.0.0.1", port=8080)
