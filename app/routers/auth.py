"""
Authentication endpoints. These are the supporting endpoints needed so
the Split Studio expense endpoints can be demonstrated end-to-end with
a real bearer token in Postman, per the assignment's note: "You may
need to add supporting services or endpoints to enable full workflow."

Full specification of every security endpoint (including password
reset and refresh) is documented in Section 2 of the report. Only
register and login are implemented in code, since those are the
minimum needed to obtain a token for the Split Studio demo.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.models import User, UserRole
from app.schemas import RegisterRequest, LoginRequest, TokenResponse, UserResponse
from app.security import hash_password, verify_password, create_access_token, create_refresh_token, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {"description": "Email already registered."},
        422: {"description": "Validation error (weak password, malformed email, etc.)."},
    },
)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user.

    Uses SQLAlchemy's ORM query builder exclusively — no raw SQL string
    concatenation occurs anywhere in this codebase, which is the
    primary defence against SQL injection described in the report.
    """
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user = User(
        full_name=payload.full_name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=UserRole.member,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )
    db.refresh(user)
    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    responses={
        401: {"description": "Incorrect email or password."},
    },
)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate a user and issue an access token and refresh token.

    The error message is intentionally identical whether the email does
    not exist or the password is wrong. Distinguishing the two cases in
    the response would let an attacker enumerate which emails are
    registered, so both failure paths return the same generic message.
    """
    user = db.query(User).filter(User.email == payload.email).first()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )

    access_token = create_access_token(subject=user.id, role=user.role.value)
    refresh_token = create_refresh_token(subject=user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
