from fastapi import APIRouter, Depends, Request

from backend.app.auth.dependencies import get_current_user_id
from backend.app.schemas import PreferencesUpdate, Profile
from backend.app.services.catalog import get_profile

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=Profile)
def profile(request: Request, user_id: str = Depends(get_current_user_id)):
    """
    Retrieve the authenticated user's profile and preferences.
    """
    return get_profile(request.app.state.container, user_id)


@router.put("/preferences", response_model=Profile)
def update_preferences(request: Request, payload: PreferencesUpdate, user_id: str = Depends(get_current_user_id)):
    """
    Update the user's explicitly preferred genres.

    This update modifies the 'initial state' for the recommender. While the
    RL agent learns from behavior, explicit preferences provide a strong
    starting point for candidate generation.
    """
    container = request.app.state.container
    profile = get_profile(container, user_id)
    profile["preferred_genres"] = payload.preferred_genres

    # Persist all profiles to the JSON store.
    container.profiles.save_all_users()
    return profile
