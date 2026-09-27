from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.user import User


def authenticate_user(
    db: Session,
    identifier: str,
    password: str
):
    """
    Authenticate a user using username or email.

    Current development database stores passwords
    as plain text. This function supports the existing
    database format.

    Password hashing will be introduced in the
    security-hardening phase.
    """

    # --------------------------------------------------
    # Find user by username OR email
    # --------------------------------------------------

    user = (
        db.query(User)
        .filter(
            or_(
                User.username == identifier,
                User.email == identifier
            )
        )
        .first()
    )

    # --------------------------------------------------
    # User does not exist
    # --------------------------------------------------

    if user is None:
        return None

    # --------------------------------------------------
    # Check account status
    # --------------------------------------------------

    if user.is_active != 1:
        return None

    # --------------------------------------------------
    # Check password
    # --------------------------------------------------

    if user.password_hash != password:
        return None

    # --------------------------------------------------
    # Return authenticated user
    # --------------------------------------------------

    return user