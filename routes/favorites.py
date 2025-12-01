from flask import Blueprint, render_template, redirect, url_for, flash
from sqlalchemy.orm import Session
from sqlalchemy import select
from models.favorite_movie_list import FavoriteMovieList
from db import engine, get_favorite_movie_ids
from tmdb import get_movie_details

favorites_bp = Blueprint("favorites", __name__, url_prefix="/favorites")

# GET /favorites
@favorites_bp.route("/", methods=["GET"])
def favorites():
    user_id = 8
    movie_ids = get_favorite_movie_ids(user_id)

    favorite_movies = []
    for mid in movie_ids:
        favorite_movies.append(get_movie_details(mid))

    return render_template("favorites.html", movies=favorite_movies)


# POST /favorites/delete/<movie_id>
@favorites_bp.route("/delete/<int:movie_id>", methods=["POST"])
def delete_favorite(movie_id):
    user_id = 8

    with Session(engine) as session:
        q = session.query(FavoriteMovieList).filter_by(
            user_id=user_id, 
            movie_id=movie_id
        )
        rows_deleted = q.delete()
        session.commit()

    if rows_deleted:
        flash("Movie removed from your favorite list!", "success")
    else:
        flash("Movie not found in your favorite list.", "error")

    return redirect(url_for("favorites.favorites"))


# POST /favorites/toggle/<movie_id>
@favorites_bp.route("/toggle/<int:movie_id>", methods=["POST"])
def toggle_favorite(movie_id):
    user_id = 8

    with Session(engine) as session:
        stmt = select(FavoriteMovieList).where(
            FavoriteMovieList.user_id == user_id,
            FavoriteMovieList.movie_id == movie_id
        )
        entry = session.execute(stmt).first()

        if entry:
            # if the movie exists in the list, then remove it.
            session.query(FavoriteMovieList).filter_by(
                user_id=user_id,
                movie_id=movie_id
            ).delete()
            session.commit()
            flash("Removed from your favorite list!", "success")
        else:
            # if the movie not exists in the list, then add it.
            session.add(FavoriteMovieList(user_id=user_id, movie_id=movie_id))
            session.commit()
            flash("Added to your favorite list!", "success")

    return redirect(url_for("movie_detail", movie_id=movie_id))