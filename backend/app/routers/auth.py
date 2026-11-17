import re

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.models.legislative import User
from app.schemas.legislative import (
    AuthTokenOut,
    UserLoginRequest,
    UserProfileOut,
    UserRegisterRequest,
    UserUpdateRequest,
)

router = APIRouter(tags=["Authentication & Private Settings"])

EMAIL_REGEX = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
bearer_scheme = HTTPBearer(auto_error=False)


def _validate_email(email: str) -> str:
    normalized = email.strip().lower()
    if not EMAIL_REGEX.match(normalized):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Informe um endereço de e-mail válido.",
        )
    return normalized


def _get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação ausente.",
        )
    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado.",
        )
    try:
        user_id = int(payload["sub"])
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido.",
        ) from exc

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado.",
        )
    return user


@router.post("/auth/register", response_model=AuthTokenOut, status_code=status.HTTP_201_CREATED)
def register_user(
    payload: UserRegisterRequest,
    db: Session = Depends(get_db),
) -> AuthTokenOut:
    """Register a private citizen account (no public citizen profile)."""
    email = _validate_email(payload.email)
    existing = db.scalar(select(User).where(User.email == email))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe uma conta cadastrada com este e-mail.",
        )

    user = User(
        email=email,
        password_hash=hash_password(payload.password),
        urgent_vote_alerts=True,
        email_digest=True,
        status_change_notifications=False,
        followed_house_slugs=["congresso-nacional", "senado-federal"],
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user_id=user.id, email=user.email)
    return AuthTokenOut(
        access_token=token,
        user=UserProfileOut.model_validate(user),
    )


@router.post("/auth/login", response_model=AuthTokenOut)
def login_user(
    payload: UserLoginRequest,
    db: Session = Depends(get_db),
) -> AuthTokenOut:
    """Authenticate an existing private citizen account."""
    email = _validate_email(payload.email)
    user = db.scalar(select(User).where(User.email == email))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos.",
        )

    token = create_access_token(user_id=user.id, email=user.email)
    return AuthTokenOut(
        access_token=token,
        user=UserProfileOut.model_validate(user),
    )


@router.get("/users/me", response_model=UserProfileOut)
def get_private_settings(current_user: User = Depends(_get_current_user)) -> UserProfileOut:
    """Return private citizen account settings."""
    return UserProfileOut.model_validate(current_user)


@router.patch("/users/me", response_model=UserProfileOut)
def update_private_settings(
    payload: UserUpdateRequest,
    current_user: User = Depends(_get_current_user),
    db: Session = Depends(get_db),
) -> UserProfileOut:
    """Update private account email, password, notification preferences, or followed houses."""
    if payload.email is not None:
        normalized_email = _validate_email(payload.email)
        if normalized_email != current_user.email:
            duplicate = db.scalar(select(User).where(User.email == normalized_email))
            if duplicate:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Este e-mail já está vinculado a outra conta.",
                )
            current_user.email = normalized_email

    if payload.new_password is not None:
        if not payload.current_password or not verify_password(
            payload.current_password, current_user.password_hash
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A senha atual informada está incorreta.",
            )
        current_user.password_hash = hash_password(payload.new_password)

    if payload.urgent_vote_alerts is not None:
        current_user.urgent_vote_alerts = payload.urgent_vote_alerts
    if payload.email_digest is not None:
        current_user.email_digest = payload.email_digest
    if payload.status_change_notifications is not None:
        current_user.status_change_notifications = payload.status_change_notifications
    if payload.followed_house_slugs is not None:
        current_user.followed_house_slugs = payload.followed_house_slugs

    db.commit()
    db.refresh(current_user)
    return UserProfileOut.model_validate(current_user)
