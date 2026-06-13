from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.analytics import Analytics
from app.models.curriculum import LearnerProfile
from app.models.user import User
from app.schemas.onboarding import LearnerProfileUpsert
from app.schemas.users import UserCreate


SUPPORTED_DOMAIN_KEYS = {"python_programming"}


def create_user(db: Session, payload: UserCreate) -> User:
    existing_user = db.scalar(select(User).where(User.email == payload.email))
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )

    if payload.auth_subject:
        existing_auth_subject = db.scalar(
            select(User).where(User.auth_subject == payload.auth_subject)
        )
        if existing_auth_subject is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this auth subject already exists.",
            )

    user = User(
        email=payload.email,
        full_name=payload.full_name,
        auth_provider=payload.auth_provider,
        auth_subject=payload.auth_subject,
    )
    db.add(user)
    db.flush()

    analytics = Analytics(user_id=user.id)
    db.add(analytics)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User could not be created because of a uniqueness conflict.",
        ) from exc

    db.refresh(user)
    return user

def sync_user(db: Session, payload: UserCreate) -> User:
    """Gets a user by auth_subject, or creates them if they don't exist.
    Does NOT auto-assign a curriculum — the onboarding flow handles that explicitly."""
    if not payload.auth_subject:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="auth_subject is required for syncing.",
        )

    user = db.scalar(select(User).where(User.auth_subject == payload.auth_subject))
    if user:
        return user

    # New user — create record only, onboarding page handles profiling
    return create_user(db, payload)


def get_user_or_404(db: Session, user_id: UUID) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    return user


def get_profile_or_404(db: Session, user_id: UUID) -> LearnerProfile:
    profile = db.scalar(select(LearnerProfile).where(LearnerProfile.user_id == user_id))
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learner profile not found.",
        )
    return profile


def upsert_learner_profile(db: Session, user_id: UUID, payload: LearnerProfileUpsert) -> LearnerProfile:
    get_user_or_404(db, user_id)

    if payload.domain_key not in SUPPORTED_DOMAIN_KEYS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported domain_key '{payload.domain_key}'.",
        )

    profile = db.scalar(select(LearnerProfile).where(LearnerProfile.user_id == user_id))
    if profile is None:
        profile = LearnerProfile(user_id=user_id)
        db.add(profile)

    profile.domain_key = payload.domain_key
    profile.goal = payload.goal
    profile.target_level = payload.target_level
    profile.time_commitment = payload.time_commitment
    profile.learning_style = payload.learning_style
    profile.motivation = payload.motivation
    profile.current_level_summary = payload.current_level_summary

    db.commit()
    db.refresh(profile)
    return profile

