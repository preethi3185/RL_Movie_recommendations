from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.app.auth.tokens import decode_access_token
from backend.app.infrastructure.auth_store import JsonAuthStore

# HTTPBearer is a FastAPI utility that automatically handles the "Authorization: Bearer <token>" header.
# We set auto_error=False so we can provide a custom error message in get_current_user_id.
bearer = HTTPBearer(auto_error=False)


def get_auth_store(request: Request) -> JsonAuthStore:
    """
    Retrieves the global auth store from the application state.

    The auth store is initialized during app startup and attached to
    request.app.state to ensure it's a singleton across the entire app.
    """
    return request.app.state.auth_store


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    auth_store: JsonAuthStore = Depends(get_auth_store),
) -> str:
    """
    FastAPI dependency that enforces authentication for protected routes.

    The Flow:
    1. Extract the Bearer token from the Authorization header.
    2. Decode and validate the JWT to extract the user ID.
    3. Verify that the user ID still exists in the system.
    """
    if credentials is None or credentials.scheme.lower() != "bearer":
        # The request is missing the Authorization header or using the wrong scheme.
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    # Attempt to decode the JWT. This checks the signature and expiration.
    user_id = decode_access_token(credentials.credentials)

    if user_id is None or auth_store.get_by_id(user_id) is None:
        # The token is either malformed, expired, or the user was deleted from the system.
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    return user_id
