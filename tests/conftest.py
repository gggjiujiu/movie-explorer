import pytest
from app import create_app
import db


@pytest.fixture
def app():
    """Create Flask app configured for testing."""
    app = create_app()
    app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
    )
    return app


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture
def logged_in_client(client):
    """Test client with a logged-in user."""
    with client.session_transaction() as sess:
        sess["user_id"] = 1
    return client


# ============================================================
# Prevent ANY real database access during tests
# ============================================================
@pytest.fixture(autouse=True)
def disable_real_database(monkeypatch):
    """Automatically mock db.engine and Session so no real DB is used."""

    class FakeSession:
        """A fake SQLAlchemy session that raises errors if used."""
        def __init__(self, *args, **kwargs):
            raise RuntimeError("DB access attempted during unit test")

    # Mock engine (so create_engine never connects)
    monkeypatch.setattr(db, "engine", None)

    # Mock Session class (so Session(engine) cannot be created)
    monkeypatch.setattr(db, "Session", FakeSession)
