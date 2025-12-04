import pytest
from app import create_app
from flask import session


# -------------------------------------------------------
# Fixtures
# -------------------------------------------------------
@pytest.fixture
def app():
    app = create_app()
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test"   # for session
    return app


@pytest.fixture
def client(app):
    return app.test_client()


# -------------------------------------------------------
# Helper to simulate login
# -------------------------------------------------------
def login(client, user_id=1):
    with client.session_transaction() as sess:
        sess["user_id"] = user_id


# -------------------------------------------------------
# User not logged in → should redirect
# -------------------------------------------------------
def test_favorites_requires_login(client, monkeypatch):

    # mock: 避免實際呼叫 DB
    monkeypatch.setattr("routes.favorites.get_favorite_movie_ids", lambda user_id: [])

    response = client.get("/favorites/", follow_redirects=True)

    assert b"Please log in first." in response.data
    assert response.status_code == 200


# -------------------------------------------------------
# Logged-in user → should display favorites page
# -------------------------------------------------------
def test_favorites_logged_in(client, monkeypatch):
    login(client, user_id=123)

    monkeypatch.setattr("routes.favorites.get_favorite_movie_ids", lambda user_id: [111])
    monkeypatch.setattr("routes.favorites.get_movie_details", lambda movie_id: {
        "id": movie_id,
        "title": "Fake Movie"
    })

    response = client.get("/favorites/")

    assert b"Favorite Movies" in response.data
    assert b"Fake Movie" in response.data


# -------------------------------------------------------
# toggle_favorite → should add a new favorite
# -------------------------------------------------------
def test_toggle_favorite_add(client, monkeypatch):
    login(client, 1)

    # Mock is_favorite = False
    monkeypatch.setattr("routes.favorites.is_favorite", lambda u, m: False)

    # Track whether add_favorite_movie 被呼叫
    called = {"add": False}

    def fake_add(u, m):
        called["add"] = True
        return True

    monkeypatch.setattr("routes.favorites.add_favorite_movie", fake_add)

    response = client.post("/favorites/toggle/123", follow_redirects=True)

    assert called["add"] == True
    assert b"Added to your favorite list!" in response.data


# -------------------------------------------------------
# toggle_favorite → should remove an existing favorite
# -------------------------------------------------------
def test_toggle_favorite_remove(client, monkeypatch):
    login(client, 1)

    # Mock is_favorite = True
    monkeypatch.setattr("routes.favorites.is_favorite", lambda u, m: True)

    called = {"delete": False}

    def fake_delete(u, m):
        called["delete"] = True
        return 1

    monkeypatch.setattr("routes.favorites.delete_favorite_movie", fake_delete)

    response = client.post("/favorites/toggle/123", follow_redirects=True)

    assert called["delete"] == True
    assert b"Removed from your favorite list!" in response.data

# -------------------------------------------------------
# delete_favorite → delete failed (0 rows deleted)
# -------------------------------------------------------
def test_delete_favorite_fail(client, monkeypatch):
    login(client, 1)

    # Mock delete_favorite_movie → returns 0 (delete failed)
    monkeypatch.setattr("routes.favorites.delete_favorite_movie", lambda u, m: 0)

    response = client.post("/favorites/delete/999", follow_redirects=True)

    assert b"Movie not found in your favorite list." in response.data

# -------------------------------------------------------
# delete_favorite → should call delete() successfully
# -------------------------------------------------------
def test_delete_favorite(client, monkeypatch):
    login(client, 1)

    called = {"delete": False}

    def fake_delete(u, m):
        called["delete"] = True
        return 1

    monkeypatch.setattr("routes.favorites.delete_favorite_movie", fake_delete)

    response = client.post("/favorites/delete/456", follow_redirects=True)

    assert called["delete"] is True
    assert b"Movie removed from your favorite list!" in response.data

# -------------------------------------------------------
# toggle_favorite → remove failed (delete returned 0)
# -------------------------------------------------------
def test_toggle_favorite_remove_fail(client, monkeypatch):
    login(client, 1)

    monkeypatch.setattr("routes.favorites.is_favorite", lambda u, m: True)

    def fake_delete(u, m):
        return 0  # delete failed

    monkeypatch.setattr("routes.favorites.delete_favorite_movie", fake_delete)

    response = client.post("/favorites/toggle/123", follow_redirects=True)

    assert b"Failed to remove movie." in response.data
