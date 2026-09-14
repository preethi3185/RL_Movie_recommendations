"""Enrich the local movie catalog with TMDB poster metadata.

Usage:
    $env:TMDB_API_KEY = "your-key"
    python scripts/enrich_movie_metadata.py
"""

import argparse
import os
import re
import unicodedata
from pathlib import Path

import pandas as pd
import requests

TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"


def normalize_title(value: object) -> str:
    """
    Cleans and normalizes movie titles for better matching against the TMDB API.

    Steps:
    1. Remove accents/special characters (Unicode NFKD).
    2. Convert to lowercase.
    3. Replace '&' with 'and' and remove non-alphanumeric characters.
    4. Collapse multiple spaces into one.
    """
    if value is None:
        return ""
    text = str(value).strip()
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = text.replace("&", " and ")
    text = text.replace("-", " ")
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    text = text.strip()
    return text


def title_variants(title: str) -> list[str]:
    """
    Generates multiple versions of a movie title to increase the chance of a TMDB match.

    Example: "The Matrix (1999)" -> ["The Matrix (1999)", "The Matrix", "matrix"]
    """
    raw = str(title).strip()
    candidates = []
    seen: set[str] = set()

    for candidate in [raw, raw.replace("&", "and")]:
        if candidate and candidate not in seen:
            candidates.append(candidate)
            seen.add(candidate)

    # Handle titles with separators (e.g., "Star Wars - A New Hope")
    for separator in [":", " - ", " — ", "(", ")", "/"]:
        if separator in raw:
            base = raw.split(separator)[0].strip()
            if base and base not in seen:
                candidates.append(base)
                seen.add(base)

    normalized = normalize_title(raw)
    # Try removing common leading articles (The, A, An)
    for candidate in [normalized, re.sub(r"^(the|a|an) ", "", normalized)]:
        if candidate and candidate not in seen:
            candidates.append(candidate)
            seen.add(candidate)

    return [candidate for candidate in candidates if candidate]


def parse_year(value: object) -> int | None:
    parsed = pd.to_datetime(value, dayfirst=True, errors="coerce")
    return int(parsed.year) if not pd.isna(parsed) else None


def score_result(title: str, year: int | None, result: dict[str, object]) -> int:
    """
    Heuristic scoring system to determine the best match from TMDB search results.

    Weights:
    - Exact match (normalized): +150 (Very strong)
    - Partial match: +80 (Strong)
    - Prefix match (first 8 chars): +30 (Weak)
    - Year match: +40 (Strong)
    - Near year match (off by 1): +10 (Weak)
    - Has poster: +25 (Necessary for UI)
    - Has backdrop: +5 (Nice to have)
    """
    query = normalize_title(title)
    result_title = normalize_title(result.get("title") or result.get("original_title") or "")
    result_year = None
    release_date = result.get("release_date")
    if isinstance(release_date, str) and len(release_date) >= 4:
        try:
            result_year = int(release_date[:4])
        except ValueError:
            result_year = None

    score = 0
    if result_title == query:
        score += 150
    elif query in result_title or result_title in query:
        score += 80
    elif result_title.startswith(query[: min(len(query), 8)]):
        score += 30

    if year and result_year == year:
        score += 40
    elif year and result_year and abs(result_year - year) == 1:
        score += 10

    if result.get("poster_path"):
        score += 25
    if result.get("backdrop_path"):
        score += 5
    return score


def find_movie(api_key: str, title: str, year: int | None) -> dict[str, object]:
    """
    Queries TMDB for a movie and selects the highest-scoring match.
    """
    best_match: dict[str, object] | None = None
    best_score = -1

    # Generate a set of search queries to try based on the title variants.
    search_queries = []
    for variant in title_variants(title):
        search_queries.append(variant)
        if variant != normalize_title(title):
            search_queries.append(normalize_title(title))

    unique_queries = []
    seen_queries: set[str] = set()
    for query in search_queries:
        normalized_query = normalize_title(query)
        if normalized_query and normalized_query not in seen_queries:
            unique_queries.append(query)
            seen_queries.add(normalized_query)

    for query in unique_queries:
        params: dict[str, object] = {"api_key": api_key, "query": query, "include_adult": "false", "page": 1}
        if year:
            params["year"] = year

        response = requests.get(TMDB_SEARCH_URL, params=params, timeout=20)
        response.raise_for_status()
        results = response.json().get("results", [])

        for result in results:
            current_score = score_result(title, year, result)
            if current_score <= best_score:
                continue
            # We only accept results that actually have a poster image.
            if not result.get("poster_path"):
                continue
            best_match = result
            best_score = current_score

    if best_match is None:
        return {"tmdb_id": None, "poster_url": None, "backdrop_url": None}

    poster_path = best_match.get("poster_path")
    backdrop_path = best_match.get("backdrop_path")
    return {
        "tmdb_id": best_match.get("id"),
        "poster_url": f"{IMAGE_BASE_URL}{poster_path}",
        "backdrop_url": f"{IMAGE_BASE_URL}{backdrop_path}" if backdrop_path else None,
    }


def enrich(input_path: Path, output_path: Path, unmatched_path: Path, api_key: str) -> None:
    """
    Main orchestration function: reads the movie list and enriches it with TMDB data.
    """
    movies = pd.read_csv(input_path)
    existing = {}
    if output_path.exists():
        existing_frame = pd.read_csv(output_path).fillna("")
        existing = {int(row["Movie_ID"]): row.to_dict() for _, row in existing_frame.iterrows()}

    # Only process movies that don't already have a valid poster URL in the existing metadata file.
    existing_poster_ids = {
        movie_id
        for movie_id, metadata in existing.items()
        if str(metadata.get("poster_url", "")).strip()
    }
    pending_movies = movies[~movies["Movie_ID"].astype(int).isin(existing_poster_ids)]
    records = [
        existing[int(movie["Movie_ID"])]
        for _, movie in movies.iterrows()
        if int(movie["Movie_ID"]) in existing_poster_ids
    ]
    unmatched = []
    total = len(pending_movies)
    print(f"Found {total} movies with missing poster URLs.")
    for index, (_, movie) in enumerate(pending_movies.iterrows(), start=1):
        title = str(movie.get("Movie_Title", "")).strip()
        if not title:
            continue
        movie_id = int(movie["Movie_ID"])
        try:
            metadata = find_movie(api_key, title, parse_year(movie.get("Movie_Release_Date")))
        except requests.RequestException:
            print(f"Skipping {title!r}: TMDB request failed")
            metadata = {"tmdb_id": None, "poster_url": None, "backdrop_url": None}
        if metadata["poster_url"] is None:
            unmatched.append({"Movie_ID": movie_id, "Movie_Title": title})
        records.append({"Movie_ID": movie_id, **metadata})
        print(f"[{index}/{total}] {title}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_frame = pd.DataFrame(records)
    matched_count = int(metadata_frame["poster_url"].fillna("").astype(str).str.strip().ne("").sum()) if not metadata_frame.empty else 0
    if matched_count == 0:
        raise RuntimeError(
            "TMDB enrichment returned no poster URLs. "
            "Check the API key and network access; no metadata file was written."
        )
    metadata_frame.to_csv(output_path, index=False)
    pd.DataFrame(unmatched).to_csv(unmatched_path, index=False)
    print(f"Saved poster metadata to {output_path}")
    print(f"Unmatched movies saved to {unmatched_path}: {len(unmatched)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add TMDB poster URLs to the local catalog.")
    parser.add_argument("--input", default="data/movies.csv")
    parser.add_argument("--output", default="data/poster_metadata.csv")
    parser.add_argument("--unmatched", default="data/unmatched_movies.csv")
    args = parser.parse_args()
    api_key = os.getenv("TMDB_API_KEY")
    if not api_key:
        raise SystemExit("TMDB_API_KEY is required. Set it in your environment before running this script.")
    enrich(Path(args.input), Path(args.output), Path(args.unmatched), api_key)
