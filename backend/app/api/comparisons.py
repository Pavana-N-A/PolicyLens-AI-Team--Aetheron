from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import User, Comparison, ComparisonPolicy
from app.schemas.schemas import ComparisonCreateRequest, ComparisonResponse
from app.api.deps import get_current_user
from app.services.comparison_service import comparison_service

router = APIRouter(prefix="/api/comparisons", tags=["Comparisons"])

@router.post("", response_model=ComparisonResponse)
def create_comparison(
    req: ComparisonCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if len(req.policy_ids) < 2:
        raise HTTPException(status_code=400, detail="Please select at least two policies to compare.")

    try:
        comp_data = comparison_service.compare_policies(
            db=db,
            policy_ids=req.policy_ids,
            priority_focus=req.priority_focus or "balanced"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Persist comparison record
    comp_record = Comparison(
        user_id=current_user.id,
        title=comp_data["title"],
        priority_focus=req.priority_focus or "balanced",
        tradeoff_summary=comp_data["tradeoff_summary"]
    )
    db.add(comp_record)
    db.commit()
    db.refresh(comp_record)

    for pid in req.policy_ids:
        cp = ComparisonPolicy(comparison_id=comp_record.id, policy_id=pid)
        db.add(cp)
    db.commit()

    return {
        "id": comp_record.id,
        "title": comp_record.title,
        "priority_focus": comp_record.priority_focus,
        "tradeoff_summary": comp_record.tradeoff_summary,
        "columns": comp_data["columns"],
        "created_at": comp_record.created_at
    }

@router.get("/{comparison_id}", response_model=ComparisonResponse)
def get_comparison(
    comparison_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    comp = db.query(Comparison).filter(Comparison.id == comparison_id, Comparison.user_id == current_user.id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Comparison record not found.")

    p_ids = [cp.policy_id for cp in comp.policies]
    comp_data = comparison_service.compare_policies(db, policy_ids=p_ids, priority_focus=comp.priority_focus)

    return {
        "id": comp.id,
        "title": comp.title,
        "priority_focus": comp.priority_focus,
        "tradeoff_summary": comp.tradeoff_summary,
        "columns": comp_data["columns"],
        "created_at": comp.created_at
    }
