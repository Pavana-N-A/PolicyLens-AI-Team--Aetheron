from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import User
from app.schemas.schemas import HospitalSearchResponse
from app.api.deps import get_current_user
from app.services.hospital_service import hospital_service

router = APIRouter(prefix="/api/hospitals", tags=["Hospitals"])

@router.get("/search", response_model=HospitalSearchResponse)
def search_hospitals(
    city: Optional[str] = None,
    name: Optional[str] = None,
    state: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    res = hospital_service.search_hospitals(
        db=db,
        user_id=current_user.id,
        city=city,
        hospital_name=name,
        state=state
    )
    return res

@router.post("/import")
async def import_hospital_csv(
    file: UploadFile = File(...),
    provider_name: str = Form("Imported Hospital TPA Network"),
    verified_date: str = Form("Verified 2026"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    content = await file.read()
    try:
        decoded = content.decode("utf-8")
    except UnicodeDecodeError:
        decoded = content.decode("latin-1")

    res = hospital_service.import_csv(
        db=db,
        user_id=current_user.id,
        filename=file.filename,
        file_content=decoded,
        provider_name=provider_name,
        verified_date=verified_date
    )
    return res
