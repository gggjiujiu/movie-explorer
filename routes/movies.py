from flask import (Blueprint, render_template,
                   request, session, abort)
from tmdb import (search_movies, get_popular_movies, get_movie_genres,
                  get_movie_details, TMDB_API_KEY)
import db

movies_bp = Blueprint('movies', __name__)


@movies_bp.route("/movies", methods=["GET"])
def movie_search():
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

    user_id = session.get("user_id")
    if user_id:
        is_fav = db.is_favorite(user_id, movie_id)
    else:
        is_fav = False

    return render_template("movie_detail.html", movie=movie, is_fav=is_fav)

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
