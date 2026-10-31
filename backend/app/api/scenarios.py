from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import User
from app.schemas.schemas import (
    DiseaseScenarioRequest, DiseaseScenarioResponse,
    GeoScenarioRequest, GeoScenarioResponse
)
from app.api.deps import get_current_user
from app.services.scenario_service import scenario_service

router = APIRouter(prefix="/api/scenarios", tags=["Scenarios"])

@router.post("/disease", response_model=DiseaseScenarioResponse)
def analyze_disease(
    req: DiseaseScenarioRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        res = scenario_service.analyze_disease_scenario(
            db=db,
            policy_id=req.policy_id,
            policy_start_date=req.policy_start_date,
            first_diagnosis_date=req.first_diagnosis_date,
            disease_name=req.disease_name,
            continuous_renewals=req.continuous_renewals,
            pre_existing_or_treated_prior=req.pre_existing_or_treated_prior,
            treatment_state=req.treatment_state,
            hospital_name=req.hospital_name
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/geography", response_model=GeoScenarioResponse)
def analyze_geography(
    req: GeoScenarioRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        res = scenario_service.check_geographical_scope(
            db=db,
            policy_id=req.policy_id,
            policy_state=req.policy_state or "Karnataka",
            treatment_state=req.treatment_state or "Maharashtra",
            hospital_name=req.hospital_name
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
