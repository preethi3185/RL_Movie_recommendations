from fastapi import APIRouter, Depends, Request

from backend.app.auth.dependencies import get_current_user_id
from backend.app.schemas import Dashboard
from backend.app.services.catalog import get_dashboard

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=Dashboard)
def dashboard(request: Request, user_id: str = Depends(get_current_user_id)):
    """
    Retrieves aggregated user statistics for the dashboard view.

    This includes:
    - Total movies watched and rated.
    - Learned genre preferences (extracted from the RL Agent's Q-table).
    - Recent activity summaries.
    """
    return get_dashboard(request.app.state.container, user_id)
