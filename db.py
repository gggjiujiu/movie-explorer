import os
from sqlalchemy import create_engine, select
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session

from models.favorite_movie_list import FavoriteMovieList
from models.users import User

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

# ======================== Auth / User Query Helpers ========================


def get_user_by_email(email: str):
    """Return the User object if email exists, else None."""
    with Session(engine) as db:
        stmt = select(User).where(User.email == email)
        return db.execute(stmt).scalar_one_or_none()


def create_user(firstname: str,
                lastname: str,
                email: str,
                account: str,
                password_hash: str):
    """Insert new user into DB and return the created user."""
    new_user = User(
        firstname=firstname,
        lastname=lastname,
        email=email,
        account=account,
        password=password_hash
    )

    with Session(engine) as db:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)   # get generated id
        return new_user


# ======================== Favorite List Helpers ========================


# search for user's favorite movie list
def get_favorite_movie_ids(user_id: int):
    with Session(engine) as session:
        stmt = select(FavoriteMovieList.movie_id).where(
            FavoriteMovieList.user_id == user_id
        )
        result = session.execute(stmt).scalars().all()
        return result


# check if this movie is in favorite list
def is_favorite(user_id: int, movie_id: int) -> bool:
    with Session(engine) as session:
        stmt = select(FavoriteMovieList).where(
            FavoriteMovieList.user_id == user_id,
            FavoriteMovieList.movie_id == movie_id
        )
        return session.execute(stmt).first() is not None


# delete a movie from the favorite list
def delete_favorite_movie(user_id: int, movie_id: int) -> int:
    with Session(engine) as session:
        q = session.query(FavoriteMovieList).filter_by(
            user_id=user_id,
            movie_id=movie_id
        )
        rows_deleted = q.delete()
        session.commit()

        # Return number of rows deleted.
        return rows_deleted


# add a movie to the favorite list
def add_favorite_movie(user_id: int, movie_id: int):
    try:
        with Session(engine) as session:
            session.add(FavoriteMovieList(user_id=user_id, movie_id=movie_id))
            session.commit()
        return True   # success
    except Exception as e:
        print("Error adding favorite:", e)
        return False  # failed

# ======================== User Helpers ========================


# get user data
def get_user(user_id: int):
    with Session(engine) as db:
        stmt = select(User).where(User.id == user_id)
        return db.execute(stmt).scalar_one_or_none()


# check if email is already used by others
def email_exists(new_email, user_id):
    with Session(engine) as db:
        stmt = select(User).where(
            User.email == new_email,
            User.id != user_id
        )
        return db.execute(stmt).first() is not None


# update email
def update_user_email(user: User, new_email: str):
    with Session(engine) as db:
        user.email = new_email
        db.merge(user)
        db.commit()


# update password
def update_user_password(user: User, hashed_password: str):
    with Session(engine) as db:
        user.password = hashed_password
        db.merge(user)
        db.commit()
