from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.curriculum import LearnerProfile
from app.schemas.users import UserCreate, UserRead
from app.services.onboarding import create_user, get_user_or_404, sync_user


class UserSyncResponse(BaseModel):
    user: UserRead
    is_onboarded: bool

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/sync", response_model=UserSyncResponse, status_code=status.HTTP_200_OK)
def sync_user_route(payload: UserCreate, db: Session = Depends(get_db)) -> UserSyncResponse:
    user = sync_user(db, payload)
    has_profile = db.scalar(
        select(LearnerProfile).where(LearnerProfile.user_id == user.id)
    ) is not None
    return UserSyncResponse(
        user=UserRead.model_validate(user),
        is_onboarded=has_profile,
    )


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user_route(payload: UserCreate, db: Session = Depends(get_db)) -> UserRead:
    user = create_user(db, payload)
    return UserRead.model_validate(user)


@router.get("/{user_id}", response_model=UserRead)
def get_user_route(user_id: UUID, db: Session = Depends(get_db)) -> UserRead:
    user = get_user_or_404(db, user_id)
    return UserRead.model_validate(user)

