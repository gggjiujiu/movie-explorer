import os
import requests
import random
from flask import abort

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMG_BASE = "https://image.tmdb.org/t/p/w342"  # poster image size


class ExternalAPIError(Exception):
    """Raised when TMDB API fails or is unreachable."""
    pass


def require_tmdb_key():
    if not TMDB_API_KEY:
        abort(500, "TMDB_API_KEY is not set.")


def search_movies(query: str, year: str | None = None):
    """Call TMDb search API and return a simplified list of movies."""
    require_tmdb_key()

    params = {
        "api_key": TMDB_API_KEY,
        "query": query,
        "include_adult": False,
        "language": "en-US"
    }
    if year:
        params["year"] = year

    try:
        resp = requests.get(
            f"{TMDB_BASE_URL}/search/movie", params=params, timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        raise ExternalAPIError(f"TMDB search failed: {e}")

    movies = []
    for m in data.get("results", []):
        poster_path = m.get("poster_path")
        poster_url = TMDB_IMG_BASE + poster_path if poster_path else None
        movies.append({
            "id": m["id"],
            "title": m["title"],
            "rating": m.get("vote_average"),
            "vote_count": m.get("vote_count"),
            "poster_url": poster_url,
            "overview": m.get("overview"),
            "release_year": (m.get("release_date") or "")[:4],
            "genre_ids": m.get("genre_ids", []),
        })
    return movies


def get_popular_movies(genre_id=None, min_rating=None, year=None, limit=20):
    """
    Fetches popular movies using the /discover/movie endpoint.
    Supports filtering by genre, rating, and year directly via the API.
    Includes random pagination to ensure the homepage content varies.
    """
    require_tmdb_key()

    # Use the 'discover' endpoint instead of 'popular' to enable filtering
    endpoint = f"{TMDB_BASE_URL}/discover/movie"

    # To make the results random/fresh on every refresh,
    # we request a random page between 1 and 5.
    random_page = random.randint(1, 5)

    params = {
        "api_key": TMDB_API_KEY,
        "language": "en-US",
        "sort_by": "popularity.desc",  # Sort by popularity
        "include_adult": False,
        "include_video": False,
        "page": random_page,
    }

    # Add filter conditions to API request parameters
    if genre_id:
        params["with_genres"] = genre_id
    if min_rating:
        params["vote_average.gte"] = min_rating
    if year:
        params["primary_release_year"] = year

    try:
        resp = requests.get(endpoint, params=params, timeout=10)

        # Fallback: If the random page is out of range,
        # or if an error occurs, try fetching page 1.
        if resp.status_code != 200 or not resp.json().get("results"):
            params["page"] = 1
            resp = requests.get(endpoint, params=params, timeout=10)

        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        raise ExternalAPIError(f"TMDB popular movies failed: {e}")

    movies = []
    for m in data.get("results", [])[:limit]:
        poster_path = m.get("poster_path")
        poster_url = TMDB_IMG_BASE + poster_path if poster_path else None
        movies.append({
            "id": m["id"],
            "title": m["title"],
            "rating": m.get("vote_average"),
            "vote_count": m.get("vote_count"),
            "poster_url": poster_url,
            "release_year": (m.get("release_date") or "")[:4],
            "genre_ids": m.get("genre_ids") or [],
        })
    return movies


def get_movie_details(movie_id: int):
    """Get detailed information for a single movie by id."""
    require_tmdb_key()

    params = {"api_key": TMDB_API_KEY, "language": "en-US"}

    try:
        resp = requests.get(
            f"{TMDB_BASE_URL}/movie/{movie_id}", params=params, timeout=10
        )
        resp.raise_for_status()
        m = resp.json()
    except Exception as e:
        raise ExternalAPIError(f"TMDB movie details failed: {e}")

    poster_path = m.get("poster_path")
    return {
        "id": m["id"],
        "title": m["title"],
        "rating": m.get("vote_average"),
        "vote_count": m.get("vote_count"),
        "poster_url": TMDB_IMG_BASE + poster_path if poster_path else None,
        "overview": m.get("overview"),
        "release_year": (m.get("release_date") or "")[:4],
        "genres": [g["name"] for g in m.get("genres", [])],
        "runtime": m.get("runtime"),
    }


# to catch the genres list of TMDb for html
_genres_cache = None


def get_movie_genres():
    require_tmdb_key()

    global _genres_cache
    if _genres_cache is not None:
        return _genres_cache

    params = {
        "api_key": TMDB_API_KEY,
        "language": "en-US",
    }
    try:
        resp = requests.get(
            f"{TMDB_BASE_URL}/genre/movie/list", params=params, timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        raise ExternalAPIError(f"TMDB genre list failed: {e}")

    _genres_cache = data.get("genres", [])
    return _genres_cache
