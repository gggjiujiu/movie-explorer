from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    account: Mapped[str]
    firstname: Mapped[str]
    lastname: Mapped[str]
    email: Mapped[str]
    password: Mapped[str]
