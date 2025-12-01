from flask import Blueprint, render_template, redirect, url_for, flash, session

from db import (
    get_favorite_movie_ids,
    is_favorite,
    delete_favorite_movie,
    add_favorite_movie
)
from tmdb import get_movie_details

favorites_bp = Blueprint("favorites", __name__, url_prefix="/favorites")

def get_current_user_id():
    return session.get("user_id")

# GET /favorites
@favorites_bp.route("/", methods=["GET"])
def favorites():
    user_id = get_current_user_id()
    movie_ids = get_favorite_movie_ids(user_id)

    favorite_movies = []
    for mid in movie_ids:
        favorite_movies.append(get_movie_details(mid))

    return render_template("favorites.html", movies=favorite_movies)


# POST /favorites/delete/<movie_id>
@favorites_bp.route("/delete/<int:movie_id>", methods=["POST"])
def delete_favorite(movie_id):
    user_id = get_current_user_id()

    rows_deleted = delete_favorite_movie(user_id, movie_id)

    if rows_deleted:
        flash("Movie removed from your favorite list!", "success")
    else:
        flash("Movie not found in your favorite list.", "error")

    return redirect(url_for("favorites.favorites"))


# POST /favorites/toggle/<movie_id>
@favorites_bp.route("/toggle/<int:movie_id>", methods=["POST"])
def toggle_favorite(movie_id):
    user_id = get_current_user_id()

    # Case 1: already in favorites → remove it
    if is_favorite(user_id, movie_id):
        rows = delete_favorite_movie(user_id, movie_id)
        if rows > 0:
            flash("Removed from your favorite list!", "success")
        else:
            flash("Failed to remove movie.", "error")

        return redirect(url_for("movie_detail", movie_id=movie_id))
    
    # Case 2: not in favorites → add it
    success = add_favorite_movie(user_id, movie_id)

    if success:
        flash("Added to your favorite list!", "success")
    else:
        flash("Failed to add movie.", "error")

    return redirect(url_for("movie_detail", movie_id=movie_id))