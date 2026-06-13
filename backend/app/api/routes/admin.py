from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.assessment import AssessmentQuestion
from app.models.curriculum import Concept
from app.models.user import User
from app.schemas.admin import AdminAssessmentQuestionRead, ConceptCreate, ConceptResponse, QuestionApprovalResponse
from app.schemas.users import UserRead

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/users", response_model=list[UserRead])
def list_users(db: Session = Depends(get_db)):
    """
    List all registered users. Useful for finding user IDs during development.
    """
    return db.scalars(select(User).order_by(User.created_at.desc())).all()


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: UUID, db: Session = Depends(get_db)):
    """
    Hard-delete a user and all their data (learning paths, mastery records,
    lessons, quizzes, tutor conversations, analytics) via DB cascade.
    """
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    db.delete(user)
    db.commit()


@router.get("/questions/pending", response_model=list[AdminAssessmentQuestionRead])
def get_pending_questions(db: Session = Depends(get_db)):
    """
    Returns all questions that have not yet been approved.
    """
    stmt = select(AssessmentQuestion).where(AssessmentQuestion.is_approved == False)
    questions = db.scalars(stmt).all()
    return questions


@router.post("/questions/{question_id}/approve", response_model=QuestionApprovalResponse)
def approve_question(question_id: UUID, db: Session = Depends(get_db)):
    """
    Approves a question so it can be served to learners.
    """
    question = db.get(AssessmentQuestion, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    question.is_approved = True
    db.commit()

    return QuestionApprovalResponse(
        id=question.id,
        is_approved=True,
        message="Question successfully approved."
    )


@router.post("/concepts", response_model=ConceptResponse, status_code=status.HTTP_201_CREATED)
def create_concept(payload: ConceptCreate, db: Session = Depends(get_db)):
    """
    Creates a new curriculum concept topic.
    """
    # Check if slug already exists
    existing = db.scalar(select(Concept).where(Concept.slug == payload.slug))
    if existing:
        raise HTTPException(status_code=400, detail="Concept with this slug already exists.")

    new_concept = Concept(**payload.model_dump())
    db.add(new_concept)
    db.commit()
    db.refresh(new_concept)
    
    return new_concept
