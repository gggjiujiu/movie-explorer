from flask import (Blueprint, render_template,
                   request, redirect, url_for, session, flash, abort)
from tmdb import (search_movies, get_popular_movies, get_movie_genres,
                  get_movie_details, apply_filters, TMDB_API_KEY)

movies_bp = Blueprint('movies', __name__)


@movies_bp.route("/movies", methods=["GET"])
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


@movies_bp.route("/movies/<int:movie_id>", methods=["GET"])
def movie_detail(movie_id: int):

    movie = get_movie_details(movie_id)
    return render_template("movie_detail.html", movie=movie)


@movies_bp.route("/account", methods=["GET"])
def account():
    if 'user_id' not in session:
        flash("Please log in to view your account details.")
        return redirect(url_for('auth.home'))
    return render_template("account.html")


@movies_bp.route("/favourites", methods=["GET"])
def favourites():
    if 'user_id' not in session:
        flash("Please log in to access your favorite movies.")
        return redirect(url_for('auth.home'))
    return render_template("favourites.html")
