from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base


class FavoriteMovieList(Base):
    __tablename__ = "favorite_movie_list"

    user_id: Mapped[int] = mapped_column(primary_key=True)
    movie_id: Mapped[int] = mapped_column(primary_key=True)
