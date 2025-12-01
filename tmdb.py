import os
import requests

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMG_BASE = "https://image.tmdb.org/t/p/w342"  # poster image size

def search_movies(query: str, year: str | None = None):
    """Call TMDb search API and return a simplified list of movies."""
    params = {
        "api_key": TMDB_API_KEY,
        "query": query,
        "include_adult": False,
        "language": "en-US",
    }
    if year:
        params["year"] = year

    resp = requests.get(f"{TMDB_BASE_URL}/search/movie", params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    movies: list[dict] = []
    for m in data.get("results", []):
        movies.append({
            "id": m["id"],
            "title": m["title"],
            "rating": m.get("vote_average"),
            "vote_count": m.get("vote_count"),
            "poster_url": TMDB_IMG_BASE + m["poster_path"] if m.get("poster_path") else None,
            "overview": m.get("overview"),
            "release_year": (m.get("release_date") or "")[:4],
        })
    return movies


def get_movie_details(movie_id: int):
    """Get detailed information for a single movie by id."""
    params = {
        "api_key": TMDB_API_KEY,
        "language": "en-US",
    }
    resp = requests.get(f"{TMDB_BASE_URL}/movie/{movie_id}", params=params, timeout=10)
    resp.raise_for_status()
    m = resp.json()

    return {
        "id": m["id"],
        "title": m["title"],
        "rating": m.get("vote_average"),
        "vote_count": m.get("vote_count"),
        "poster_url": TMDB_IMG_BASE + m["poster_path"] if m.get("poster_path") else None,
        "overview": m.get("overview"),
        "release_year": (m.get("release_date") or "")[:4],
        "genres": [g["name"] for g in m.get("genres", [])],
        "runtime": m.get("runtime"),
    }
