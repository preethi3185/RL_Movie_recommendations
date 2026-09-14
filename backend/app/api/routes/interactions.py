from fastapi import APIRouter, Depends, Request

from backend.app.auth.dependencies import get_current_user_id
from backend.app.schemas import Movie, RatingRequest
from backend.app.services.catalog import get_profile, movies_by_ids

router = APIRouter(prefix="/interactions", tags=["interactions"])


@router.get("/history", response_model=list[Movie])
def history(request: Request, user_id: str = Depends(get_current_user_id)):
    """
    Retrieves the list of movies the user has already watched.
    """
    container = request.app.state.container
    profile = get_profile(container, user_id)
    return movies_by_ids(container, profile.get("watched_movies", []))


@router.get("/watchlist", response_model=list[Movie])
def watchlist(request: Request, user_id: str = Depends(get_current_user_id)):
    """
    Retrieves the user's saved watchlist.
    """
    container = request.app.state.container
    profile = get_profile(container, user_id)
    return movies_by_ids(container, profile.get("watchlist", []))


@router.post("/{movie_id}/watched", response_model=Movie)
def mark_watched(request: Request, movie_id: int, user_id: str = Depends(get_current_user_id)):
    """
    Marks a movie as watched and adds it to the user's history.
    """
    container = request.app.state.container
    container.profiles.update_history(user_id, movie_id)
    movies = movies_by_ids(container, [movie_id])
    if not movies:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Movie not found")
    return movies[0]


@router.post("/{movie_id}/rating", response_model=Movie)
def rate_movie(request: Request, movie_id: int, payload: RatingRequest, user_id: str = Depends(get_current_user_id)):
    """
    The core feedback loop endpoint.

    When a user rates a movie:
    1. The rating is sent to the FeedbackHandler.
    2. The handler maps the rating to a reward signal.
    3. The RL agent updates its Q-table for the movie's genres.
    4. User profile history is updated.
    """
    container = request.app.state.container
    container.feedback.process_feedback(user_id, movie_id, payload.rating, container.dataframe)
    movies = movies_by_ids(container, [movie_id])
    if not movies:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Movie not found")
    return movies[0]


@router.post("/{movie_id}/watchlist", response_model=Movie)
def add_watchlist(request: Request, movie_id: int, user_id: str = Depends(get_current_user_id)):
    """Adds a movie to the user's watchlist."""
    container = request.app.state.container
    container.profiles.add_to_watchlist(user_id, movie_id)
    return movies_by_ids(container, [movie_id])[0]


@router.delete("/{movie_id}/watchlist", response_model=Movie)
def remove_watchlist(request: Request, movie_id: int, user_id: str = Depends(get_current_user_id)):
    """Removes a movie from the user's watchlist."""
    container = request.app.state.container
    container.profiles.remove_from_watchlist(user_id, movie_id)
    return movies_by_ids(container, [movie_id])[0]
