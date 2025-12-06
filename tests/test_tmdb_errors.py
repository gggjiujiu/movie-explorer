from tmdb import ExternalAPIError

from routes import movies


def test_movie_detail_tmdb_error(client, monkeypatch):
    """Test that movie_detail shows error page when TMDB API fails."""

    # Force TMDB to fail by raising ExternalAPIError in get_movie_details
    monkeypatch.setattr(
        movies,
        "get_movie_details",
        lambda mid: (_ for _ in ()).throw(ExternalAPIError("TMDB down"))
    )

    resp = client.get("/movies/100")

    # Status code should reflect Service Unavailable
    assert resp.status_code == 503

    # tmdb_error.html should be rendered
    assert b"Service" in resp.data  # or whatever your error page text contains


def test_movie_search_tmdb_error(client, monkeypatch):
    """Test that movie_search shows error page when TMDB genre API fails."""

    # Mock get_popular_movies so it raises TMDB API error
    monkeypatch.setattr(
        movies,
        "get_popular_movies",
        lambda *args,
        **kwargs: (_ for _ in ()).throw(ExternalAPIError("TMDB down"))
    )

    # Also mock get_movie_genres to avoid real call (optional but safer)
    monkeypatch.setattr(movies, "get_movie_genres", lambda: [])

    resp = client.get("/movies")
    assert resp.status_code == 503
    assert b"Service" in resp.data
