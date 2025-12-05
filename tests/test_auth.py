import db
from routes import movies


# ============================================
# Helper: Mock all TMDB calls so redirects work
# ============================================
def mock_tmdb(monkeypatch):
    """Mock TMDB functions used inside movies.movie_search."""
    monkeypatch.setattr(movies, "search_movies", lambda *a, **k: [])
    monkeypatch.setattr(movies, "get_popular_movies", lambda *a, **k: [])
    monkeypatch.setattr(movies, "get_movie_genres", lambda: [])
    monkeypatch.setattr(movies, "apply_filters", lambda x, y, z: x)


# ============================================
# Home page tests
# ============================================
def test_home_redirects_when_logged_in(app, client):
    with client.session_transaction() as sess:
        sess["user_id"] = 123

    resp = client.get("/")
    assert resp.status_code == 302
    assert "/movies" in resp.headers["Location"]


def test_home_renders_login_page_when_not_logged_in(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"Login" in resp.data


# ============================================
# Login tests
# ============================================
class DummyUser:
    id = 42

    def __init__(self, ok=True):
        self._ok = ok

    def check_password(self, pw):
        return self._ok and pw == "correct123"


def test_login_success(client, monkeypatch):
    """Test successful login sets session and redirects."""
    monkeypatch.setattr(db, "get_user_by_email", lambda email: DummyUser(ok=True))

    mock_tmdb(monkeypatch)

    resp = client.post(
        "/login",
        data={"email": "a@b.c", "password": "correct123"},
        follow_redirects=True,
    )

    assert resp.status_code == 200

    with client.session_transaction() as sess:
        assert sess["user_id"] == 42


def test_login_failure_wrong_password(client, monkeypatch):
    monkeypatch.setattr(db, "get_user_by_email", lambda email: DummyUser(ok=False))

    mock_tmdb(monkeypatch)

    resp = client.post(
        "/login",
        data={"email": "a@b.c", "password": "wrong"},
        follow_redirects=True,
    )

    assert b"Invalid email or password" in resp.data


# ============================================
# Signup tests
# ============================================
def test_signup_email_already_registered(client, monkeypatch):
    monkeypatch.setattr(db, "get_user_by_email", lambda email: DummyUser())

    mock_tmdb(monkeypatch)

    resp = client.post(
        "/signup",
        data={
            "firstname": "A",
            "lastname": "B",
            "email": "a@b.c",
            "password": "pw",
        },
        follow_redirects=True,
    )

    assert b"Email already registered" in resp.data


def test_signup_success(client, monkeypatch):
    monkeypatch.setattr(db, "get_user_by_email", lambda email: None)

    class NewUser:
        id = 99

    monkeypatch.setattr(db, "create_user", lambda *a, **k: NewUser())

    mock_tmdb(monkeypatch)

    resp = client.post(
        "/signup",
        data={
            "firstname": "A",
            "lastname": "B",
            "email": "a@b.c",
            "password": "pw",
        },
        follow_redirects=True,
    )

    assert resp.status_code == 200

    with client.session_transaction() as sess:
        assert sess["user_id"] == 99


# ============================================
# Logout tests
# ============================================
def test_logout_clears_session(logged_in_client):
    resp = logged_in_client.get("/logout", follow_redirects=True)

    with logged_in_client.session_transaction() as sess:
        assert "user_id" not in sess
