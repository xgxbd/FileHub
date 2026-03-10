from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db import get_db
from app.models.user import User
from app.schemas.auth import AuthTokens, LoginRequest, RefreshRequest, RegisterRequest, UserProfile
from app.services.operation_log_service import record_operation
from app.services.auth_service import authenticate_user, issue_tokens, refresh_user_tokens, register_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserProfile, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> UserProfile:
    user = register_user(
        db=db,
        email=payload.email,
        username=payload.username,
        password=payload.password,
    )
    return UserProfile.model_validate(user)


@router.post("/login", response_model=AuthTokens)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> AuthTokens:
    user = authenticate_user(db=db, account=payload.account, password=payload.password)
    tokens = AuthTokens(**issue_tokens(user=user))
    record_operation(
        db=db,
        user=user,
        action="login",
        target_type="user",
        target_id=str(user.id),
        detail={"account": payload.account},
    )
    return tokens


@router.post("/refresh", response_model=AuthTokens)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> AuthTokens:
    return AuthTokens(**refresh_user_tokens(db=db, refresh_token=payload.refresh_token))


@router.get("/me", response_model=UserProfile)
def me(current_user: User = Depends(get_current_user)) -> UserProfile:
    return UserProfile.model_validate(current_user)
