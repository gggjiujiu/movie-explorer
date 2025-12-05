import tmdb
import db
from routes import movies


# ======================================================
# movie_search Tests
# ======================================================
def test_movie_search_uses_search_when_query(client, monkeypatch):
    """Test that movie_search uses search_movies() when q is provided."""
    monkeypatch.setattr(tmdb, "TMDB_API_KEY", "dummy")

    called = {"count": 0}

    def fake_search(q, year):
        called["count"] += 1
        return []

    monkeypatch.setattr(movies, "search_movies", fake_search)
    monkeypatch.setattr(movies, "get_popular_movies", lambda *a, **k: [])
    monkeypatch.setattr(movies, "get_movie_genres", lambda: [])

    resp = client.get("/movies?q=hello")
    assert resp.status_code == 200
    assert called["count"] == 1


def test_movie_search_uses_popular_when_no_query(client, monkeypatch):
    """Test that movie_search calls get_popular_movies() when q is empty."""
    monkeypatch.setattr(tmdb, "TMDB_API_KEY", "dummy")

    called = {"count": 0}

    def fake_popular(*a, **k):
        called["count"] += 1
        return []

    monkeypatch.setattr(movies, "get_popular_movies", fake_popular)
    monkeypatch.setattr(movies, "search_movies", lambda *a, **k: [])
    monkeypatch.setattr(movies, "get_movie_genres", lambda: [])

    resp = client.get("/movies")
    assert resp.status_code == 200
    assert called["count"] == 1


# ======================================================
# movie_detail Tests
# ======================================================
def test_movie_detail_favorite(logged_in_client, monkeypatch):
    """Test movie_detail marks the movie as favorite when DB returns True."""
    monkeypatch.setattr(tmdb, "TMDB_API_KEY", "dummy")
    monkeypatch.setattr(
        movies, "get_movie_details",
        lambda mid: {"id": mid, "title": "Test Title"}
    )
    monkeypatch.setattr(db, "is_favorite", lambda u, m: True)

    resp = logged_in_client.get("/movies/100")
    assert b"In Favorite List" in resp.data


def test_movie_detail_not_favorite(logged_in_client, monkeypatch):
    """Test movie_detail shows Add button when movie is not a favorite."""
    monkeypatch.setattr(tmdb, "TMDB_API_KEY", "dummy")
    monkeypatch.setattr(
        movies, "get_movie_details",
        lambda mid: {"id": mid, "title": "Test Title"}
    )
    monkeypatch.setattr(db, "is_favorite", lambda u, m: False)

    resp = logged_in_client.get("/movies/100")
    assert b"Add to Favorite List" in resp.data
