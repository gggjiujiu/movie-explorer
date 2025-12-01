import os
from sqlalchemy import create_engine, select
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session

from models.favorite_movie_list import FavoriteMovieList

# Create Postgres engine
url = URL.create(
    drivername="postgresql+psycopg2",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    database=os.getenv("DB_NAME"),
    query={"client_encoding": "utf8"}
)

engine = create_engine(url)


# Helper：search for user's favorite movie list
def get_favorite_movie_ids(user_id: int):
    with Session(engine) as session:
        stmt = select(FavoriteMovieList.movie_id).where(
            FavoriteMovieList.user_id == user_id
        )
        result = session.execute(stmt).scalars().all()
        return result


# Helper：check if this movie is in favorite list
def is_favorite(user_id: int, movie_id: int) -> bool:
    with Session(engine) as session:
        stmt = select(FavoriteMovieList).where(
            FavoriteMovieList.user_id == user_id,
            FavoriteMovieList.movie_id == movie_id
        )
        return session.execute(stmt).first() is not None