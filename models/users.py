from datetime import datetime
from sqlalchemy import DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column
from werkzeug.security import generate_password_hash, check_password_hash

from models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    account: Mapped[str]
    firstname: Mapped[str]
    lastname: Mapped[str]
    email: Mapped[str]
    password: Mapped[str]

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Set password（encrypted）
    def set_password(self, password_input):
        self.password = generate_password_hash(password_input)

    # Verify password
    def check_password(self, password_input):
        return check_password_hash(self.password, password_input)
