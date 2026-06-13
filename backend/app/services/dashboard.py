from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.orm import Session, selectinload

from app.models.assessment import MasteryRecord
from app.models.curriculum import Concept, LearnerProfile, LearningPath, LearningPathItem
from app.models.enums import LearningPathItemStatus
from app.schemas.assessment import MasteryRecordRead
from app.schemas.dashboard import DashboardOverviewRead, NextActionRead
from app.services.curriculum import _resolve_mastery_thresholds
from app.services.onboarding import get_profile_or_404


class DashboardService:
    @staticmethod
    def get_dashboard_overview(db: Session, user_id: UUID) -> DashboardOverviewRead:
        profile = get_profile_or_404(db, user_id)
        domain_key = profile.domain_key
        thresholds = _resolve_mastery_thresholds(profile.target_level)

        # 1. Fetch total concepts in domain
        total_concepts = db.scalar(
            select(func.count()).select_from(Concept).where(Concept.domain_key == domain_key)
        ) or 0

        # 2. Fetch Mastery Records
        mastery_records = db.scalars(
            select(MasteryRecord)
            .where(MasteryRecord.user_id == user_id)
            .options(selectinload(MasteryRecord.concept))
        ).all()

        mastery_map: list[MasteryRecordRead] = []
        weak_areas: list[MasteryRecordRead] = []
        total_mastered = 0

        for mr in mastery_records:
            read_model = MasteryRecordRead(
                concept_id=mr.concept_id,
                concept_slug=mr.concept.slug,
                concept_name=mr.concept.name,
                mastery_score=mr.mastery_score,
                quiz_accuracy=mr.quiz_accuracy,
                practice_accuracy=mr.practice_accuracy,
                consistency_score=mr.consistency_score,
                confidence=mr.confidence,
                evidence_summary=mr.evidence_summary,
                last_evaluated_at=mr.last_evaluated_at
            )
            mastery_map.append(read_model)
            
            if mr.mastery_score >= thresholds["skip"]:
                total_mastered += 1
            elif mr.mastery_score > 0 and mr.mastery_score < thresholds["review"]:
                weak_areas.append(read_model)

        progress_percentage = (total_mastered / total_concepts * 100) if total_concepts > 0 else 0.0

        # 3. Determine Next Action
        next_action = None
        active_path = db.scalar(
            select(LearningPath)
            .where(LearningPath.user_id == user_id, LearningPath.is_active == True)
            .options(selectinload(LearningPath.items).selectinload(LearningPathItem.concept))
            .order_by(LearningPath.version.desc())
        )

        if active_path:
            # Find first pending item
            sorted_items = sorted(active_path.items, key=lambda x: x.position)
            for item in sorted_items:
                if item.status == LearningPathItemStatus.PENDING:
                    next_action = NextActionRead(
                        learning_path_item_id=item.id,
                        concept_id=item.concept_id,
                        concept_name=item.concept.name,
                        item_type=item.item_type,
                        reason=item.unlock_condition
                    )
                    break

        return DashboardOverviewRead(
            user_id=user_id,
            domain_key=domain_key,
            total_concepts_mastered=total_mastered,
            total_concepts_in_domain=total_concepts,
            overall_progress_percentage=round(progress_percentage, 2),
            mastery_map=mastery_map,
            weak_areas=weak_areas,
            next_action=next_action
        )
