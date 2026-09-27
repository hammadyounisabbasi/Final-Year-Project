from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User


# ==========================================================
# HTTP BEARER AUTHENTICATION
# ==========================================================

security = HTTPBearer()


# ==========================================================
# CURRENT USER
# ==========================================================

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Get the currently authenticated user from JWT.
    """

    token = credentials.credentials

    # ------------------------------------------------------
    # Decode JWT
    # ------------------------------------------------------

    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={
                "WWW-Authenticate": "Bearer"
            }
        )

    # ------------------------------------------------------
    # Get user ID from JWT
    # ------------------------------------------------------

    user_id = payload.get("sub")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={
                "WWW-Authenticate": "Bearer"
            }
        )

    # ------------------------------------------------------
    # Find user in database
    # ------------------------------------------------------

    user = (
        db.query(User)
        .filter(User.user_id == int(user_id))
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists",
            headers={
                "WWW-Authenticate": "Bearer"
            }
        )

    # ------------------------------------------------------
    # Check account status
    # ------------------------------------------------------

    if user.is_active != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    return user