import db
from routes import favorites
from routes import movies


# ======================================================
# GET /favorites Tests
# ======================================================
def test_favorites_page_requires_login(client):
    """Test that /favorites redirects for anonymous users."""
    resp = client.get("/favorites/", follow_redirects=False)
    assert resp.status_code == 302


def test_favorites_page_lists_movies(logged_in_client, monkeypatch):
    """Test that /favorites displays the correct movie titles."""

    # Mock DB: user has movies [1, 2] in favorites
    monkeypatch.setattr(db, "get_favorite_movie_ids", lambda uid: [1, 2])

    # Mock TMDB: details for these movies
    fake_movies = {
        1: {"id": 1, "title": "Movie A"},
        2: {"id": 2, "title": "Movie B"},
    }
    monkeypatch.setattr(favorites, "get_movie_details",
                        lambda mid: fake_movies[mid])

    resp = logged_in_client.get("/favorites/", follow_redirects=True)

    assert resp.status_code == 200
    assert b"Movie A" in resp.data
    assert b"Movie B" in resp.data


def test_delete_favorite_success(logged_in_client, monkeypatch):
    """Deleting a movie successfully should flash a success message."""

    monkeypatch.setattr(db, "delete_favorite_movie",
                        lambda uid, mid: 1)
    monkeypatch.setattr(db, "get_favorite_movie_ids",
                        lambda uid: [])

    resp = logged_in_client.post("/favorites/delete/10", follow_redirects=True)

    assert b"Movie removed from your favorite list!" in resp.data


def test_delete_favorite_fail(logged_in_client, monkeypatch):
    """Failing to delete should flash an error message."""

    monkeypatch.setattr(db, "delete_favorite_movie",
                        lambda uid, mid: 0)
    monkeypatch.setattr(db, "get_favorite_movie_ids",
                        lambda uid: [])

    resp = logged_in_client.post("/favorites/delete/10", follow_redirects=True)

    assert b"Movie not found in your favorite list." in resp.data


# ======================================================
# POST /favorites/toggle Tests
# ======================================================
def test_toggle_adds_when_not_favorite(logged_in_client, monkeypatch):
    """
    When the movie is NOT already a favorite:
    - favorites.toggle_favorite should call add_favorite_movie()
    - then redirect to movie_detail()
    """

    # Mock DB behavior for adding
    monkeypatch.setattr(db, "is_favorite", lambda u, m: False)
    monkeypatch.setattr(db, "add_favorite_movie", lambda u, m: True)
    monkeypatch.setattr(db, "delete_favorite_movie", lambda u, m: 0)

    # movie_detail() runs after redirect → must mock TMDB call
    monkeypatch.setattr(movies, "get_movie_details",
                        lambda mid: {"id": mid, "title": "Fake"})

    resp = logged_in_client.post("/favorites/toggle/10",
                                 follow_redirects=True)

    assert b"Added to your favorite list" in resp.data


def test_toggle_removes_when_favorite(logged_in_client, monkeypatch):
    """
    When the movie IS already a favorite:
    - favorites.toggle_favorite should call delete_favorite_movie()
    - then redirect to movie_detail()
    """

    monkeypatch.setattr(db, "is_favorite", lambda u, m: True)
    monkeypatch.setattr(db, "delete_favorite_movie", lambda u, m: 1)
    monkeypatch.setattr(db, "add_favorite_movie", lambda u, m: False)

    # Mock redirect target movie_detail()
    monkeypatch.setattr(movies, "get_movie_details",
                        lambda mid: {"id": mid, "title": "Fake"})

    resp = logged_in_client.post("/favorites/toggle/10",
                                 follow_redirects=True)

    assert b"Removed from your favorite list" in resp.data


def test_toggle_add_failed(logged_in_client, monkeypatch):
    """When add_favorite_movie fails, it should show an error message."""

    monkeypatch.setattr(db, "is_favorite", lambda u, m: False)
    monkeypatch.setattr(db, "add_favorite_movie", lambda u, m: False)

    # mock movie_detail to avoid calling TMDB
    monkeypatch.setattr(movies, "get_movie_details",
                        lambda mid: {"id": mid, "title": "Fake"})

    resp = logged_in_client.post("/favorites/toggle/10",
                                 follow_redirects=True)

    assert b"Failed to add movie." in resp.data


def test_toggle_remove_failed(logged_in_client, monkeypatch):
    """When delete_favorite_movie fails, it should show an error message."""

    monkeypatch.setattr(db, "is_favorite", lambda u, m: True)
    monkeypatch.setattr(db, "delete_favorite_movie", lambda u, m: 0)

    monkeypatch.setattr(movies, "get_movie_details",
                        lambda mid: {"id": mid, "title": "Fake"})

    resp = logged_in_client.post("/favorites/toggle/10",
                                 follow_redirects=True)

    assert b"Failed to remove movie." in resp.data


def test_toggle_requires_login(client):
    """toggle_favorite should redirect when user is not logged in."""
    resp = client.post("/favorites/toggle/10", follow_redirects=False)
    assert resp.status_code == 302
