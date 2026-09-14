from fastapi import APIRouter, Depends, Query, Request

from backend.app.auth.dependencies import get_current_user_id
from backend.app.schemas import Recommendation
from backend.app.services.catalog import get_recommendations

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("", response_model=list[Recommendation])
def recommendations(request: Request, limit: int = Query(12, ge=1, le=50), offset: int = Query(0, ge=0), user_id: str = Depends(get_current_user_id)):
    """
    Fetches personalized movie recommendations for the authenticated user.

    This endpoint implements a Hybrid Recommendation Strategy:
    1. Candidate Generation: Uses the ContentRecommender to find movies
       similar to the user's favorite genres.
    2. RL Reranking: The RL Agent reranks these candidates based on the
       user's learned preferences (Q-values).
    3. Scoring: Predicts a final score for each movie to determine the final order.
    """
    return get_recommendations(request.app.state.container, user_id, limit, offset)
