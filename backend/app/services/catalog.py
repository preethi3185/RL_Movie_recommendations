from typing import Any

import pandas as pd

from backend.app.infrastructure.container import AppContainer


def _clean_value(value: Any) -> Any:
    """
    Sanitizes data values for JSON serialization.

    Pandas and NumPy often use custom types (e.g., np.int64) that the standard
    json library cannot serialize. This function converts those types to
    native Python types (e.g., int, float, str).
    """
    if pd.isna(value):
        return ""
    if hasattr(value, "item"):
        # .item() converts a NumPy scalar to a native Python scalar.
        return value.item()
    return value


def movie_from_row(row: pd.Series) -> dict[str, Any]:
    """Converts a Pandas Series (movie row) into a clean dictionary for API responses."""
    return {
        "movie_id": int(row["Movie_ID"]),
        "title": str(_clean_value(row.get("Movie_Title", ""))),
        "genre": str(_clean_value(row.get("Movie_Genre", ""))),
        "overview": str(_clean_value(row.get("Movie_Overview", ""))),
        "vote": float(_clean_value(row.get("Movie_Vote", 0)) or 0),
        "popularity": float(_clean_value(row.get("Movie_Popularity", 0)) or 0),
        "release_date": str(_clean_value(row.get("Movie_Release_Date", ""))),
        "runtime": float(_clean_value(row.get("Movie_Runtime", 0)) or 0),
        "director": str(_clean_value(row.get("Movie_Director", ""))),
        "tagline": str(_clean_value(row.get("Movie_Tagline", ""))),
        "poster_url": str(_clean_value(row.get("poster_url", ""))) or None,
    }


def get_profile(container: AppContainer, user_id: str) -> dict[str, Any]:
    """Retrieves user profile or creates one if it doesn't exist."""
    profile = container.profiles.get_profile(user_id)
    return profile or container.profiles.create_profile(user_id)


def get_recommendations(container: AppContainer, user_id: str, limit: int, offset: int) -> list[dict[str, Any]]:
    """
    Core Hybrid Recommendation Logic.

    This function implements a two-stage pipeline:
    1. Retrieval (Candidate Generation): We find a broad set of movies that
       match the user's preferred genres using ContentRecommender.
    2. Reranking (Personalization): We use the RL agent's learned Q-values
       to sort these candidates based on the user's behavioral history.
    """
    profile = get_profile(container, user_id)

    # Stage 1: Generate Candidates.
    if profile.get("preferred_genres"):
        # Fetch movies matching user's explicit preferences.
        candidates = container.recommender.get_candidates_by_genre(
            profile["preferred_genres"], top_n=max(offset + limit * 5, 100)
        )
    else:
        # Cold Start: If no preferences, use random samples to encourage discovery.
        candidates = container.dataframe.sample(n=min(max(offset + limit * 5, 100), len(container.dataframe)))

    # Filter out movies the user has already watched to avoid redundant suggestions.
    candidates = candidates[~candidates["Movie_ID"].isin(profile.get("watched_movies", []))]

    # Stage 2: RL Reranking.
    # The RL agent sorts the candidates based on the expected reward (Q-value) for the genres.
    ranked, reasons = container.rl_agent.get_reranked_list(candidates, profile)

    # Paginate the ranked list for the UI.
    paginated_ranked = ranked.iloc[offset : offset + limit]

    results = []
    for index, (_, row) in enumerate(paginated_ranked.iterrows()):
        movie = movie_from_row(row)
        genres = str(row.get("Movie_Genre", "")).split(",")
        q_values = [container.rl_agent.q_table.get(genre.strip(), 0.0) for genre in genres]

        # Get the specific reason provided by the RL agent for this movie.
        original_index = ranked.index.get_loc(row.name)
        movie["reason"] = reasons[original_index] if original_index < len(reasons) else "Suggested for you"

        # Predicted Score Calculation:
        # We map the average Q-value (typically -1 to 1) to a 1-5 star scale.
        # Formula: 3.0 (neutral) + (avg_q * 2)
        # Result: -1.0 Q -> 1 star; 0.0 Q -> 3 stars; 1.0 Q -> 5 stars.
        movie["predicted_score"] = round(3.0 + (sum(q_values) / len(q_values) * 2 if q_values else 0), 2)
        results.append(movie)
    return results


def search_movies(container: AppContainer, query: str, page: int, limit: int) -> dict[str, Any]:
    """Searches for movies by title or genre and returns paginated results."""
    query = query.strip()
    frame = container.dataframe
    if query:
        # Case-insensitive search across title and genre columns.
        title_matches = frame[frame["Movie_Title"].str.contains(query, case=False, na=False)]
        genre_matches = frame[frame["Movie_Genre"].str.contains(query, case=False, na=False)]
        frame = pd.concat([title_matches, genre_matches]).drop_duplicates(subset="Movie_ID")
    total = len(frame)
    start = max(page - 1, 0) * limit
    rows = [movie_from_row(row) for _, row in frame.iloc[start:start + limit].iterrows()]
    return {"items": rows, "page": page, "limit": limit, "total": total}


def movies_by_ids(container: AppContainer, movie_ids: list[int]) -> list[dict[str, Any]]:
    """Helper to fetch multiple movies by their IDs while preserving order."""
    frame = container.dataframe[container.dataframe["Movie_ID"].isin(movie_ids)]
    by_id = {int(row["Movie_ID"]): movie_from_row(row) for _, row in frame.iterrows()}
    return [by_id[movie_id] for movie_id in movie_ids if movie_id in by_id]


def get_dashboard(container: AppContainer, user_id: str) -> dict[str, Any]:
    """Aggregates user statistics and RL-learned preferences for the dashboard."""
    profile = get_profile(container, user_id)
    # Extract the current Q-values for the user's preferred genres to show "preference strength".
    preferences = [
        {"genre": genre, "score": round(float(container.rl_agent.q_table.get(genre, 0.0)), 3)}
        for genre in profile.get("preferred_genres", [])
    ]
    return {
        "movies_watched": len(profile.get("watched_movies", [])),
        "movies_rated": profile.get("total_ratings", 0),
        "average_rating": round(float(profile.get("avg_rating", 0.0)), 2),
        "genre_preferences": preferences,
    }
