from flask import Blueprint, render_template, redirect, url_for, flash, session
from sqlalchemy.orm import Session
from sqlalchemy import select
from models.favorite_movie_list import FavoriteMovieList
from db import (
    get_favorite_movie_ids,
    delete_favorite_movie,
    toggle_favorite_movie
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

    added = toggle_favorite_movie(user_id, movie_id)

    if added:
        flash("Added to your favorite list!", "success")
    else:
        flash("Removed from your favorite list!", "success")

    return redirect(url_for("movie_detail", movie_id=movie_id))