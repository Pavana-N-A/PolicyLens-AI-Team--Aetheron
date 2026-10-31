import os
import uuid
import shutil
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from app.database import get_db, UPLOADS_DIR, BACKEND_DIR
from app.models.models import User, Policy, PolicyPage, PolicyClause, PolicyField
from app.schemas.schemas import (
    PolicySummaryResponse, PolicyDetailResponse,
    PolicyClauseSchema, PolicyPageSchema, ClauseUpdateRequest
)
from app.api.deps import get_current_user
from app.services.pdf_service import pdf_service
from app.services.clause_extractor import clause_extractor
from app.services.retrieval_service import retrieval_service

router = APIRouter(prefix="/api/policies", tags=["Policies"])

@router.post("/upload", response_model=PolicySummaryResponse)
async def upload_policy(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    # User uploads directory
    user_upload_dir = os.path.join(UPLOADS_DIR, current_user.id)
    os.makedirs(user_upload_dir, exist_ok=True)

    file_id = str(uuid.uuid4())
    stored_filename = f"{file_id}.pdf"
    stored_path = os.path.join(user_upload_dir, stored_filename)

    # Save to disk
    contents = await file.read()
    if len(contents) > 30 * 1024 * 1024: # 30 MB limit
        raise HTTPException(status_code=400, detail="File size exceeds the 30 MB limit.")

    # Validate PDF magic number
    if not contents.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="Invalid PDF file header.")

    with open(stored_path, "wb") as f:
        f.write(contents)

    file_hash = pdf_service.calculate_file_hash(stored_path)

    # Check for duplicate policy
    existing = db.query(Policy).filter(
        Policy.user_id == current_user.id,
        Policy.file_hash == file_hash
    ).first()
    if existing:
        return existing

    # Create policy record
    rel_path = os.path.relpath(stored_path, BACKEND_DIR)
    policy = Policy(
        id=file_id,
        user_id=current_user.id,
        original_filename=file.filename,
        stored_relative_path=rel_path,
        file_hash=file_hash,
        extraction_status="Extracting"
    )
    db.add(policy)
    db.commit()

    # Extract text with hybrid PDF pipeline
    try:
        extraction_result = pdf_service.extract_document(stored_path)
        policy.page_count = extraction_result["page_count"]
        policy.ocr_used = extraction_result["ocr_used"]
        policy.ocr_confidence_avg = extraction_result["ocr_confidence_avg"]

        pages_data = []
        for p in extraction_result["pages"]:
            page_obj = PolicyPage(
                policy_id=policy.id,
                page_number=p["page_number"],
                extracted_text=p["text"],
                extraction_method=p["extraction_method"],
                ocr_confidence=p["ocr_confidence"],
                has_tables=p["has_tables"],
                needs_review=p["needs_review"]
            )
            db.add(page_obj)
            pages_data.append(p)

        db.commit()

        # Build SQLite FTS5 index
        retrieval_service.index_policy_pages(db, policy.id, pages_data)

        # Run clause analysis & normalize fields
        clause_extractor.analyze_and_populate_policy(db, policy.id)
        db.refresh(policy)

    except Exception as e:
        policy.extraction_status = "Failed"
        db.commit()
        raise HTTPException(status_code=500, detail=f"PDF extraction failed: {str(e)}")

    return policy

@router.get("", response_model=List[PolicySummaryResponse])
def list_policies(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Policy).filter(Policy.user_id == current_user.id).order_by(Policy.upload_date.desc()).all()

@router.get("/{policy_id}", response_model=PolicyDetailResponse)
def get_policy(policy_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    policy = db.query(Policy).filter(Policy.id == policy_id, Policy.user_id == current_user.id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy document not found.")
    return policy

@router.delete("/{policy_id}")
def delete_policy(policy_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    policy = db.query(Policy).filter(Policy.id == policy_id, Policy.user_id == current_user.id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy document not found.")

    # Remove file on disk
    full_path = os.path.join(BACKEND_DIR, policy.stored_relative_path)
    if os.path.exists(full_path):
        try:
            os.remove(full_path)
        except Exception:
            pass

    # Remove FTS5 index
    retrieval_service.remove_policy_index(db, policy.id)

    db.delete(policy)
    db.commit()
    return {"message": "Policy document and associated extracted data deleted successfully."}

@router.post("/{policy_id}/analyze")
def reanalyze_policy(policy_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    policy = db.query(Policy).filter(Policy.id == policy_id, Policy.user_id == current_user.id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy document not found.")

    # Clear existing clauses & fields
    db.query(PolicyClause).filter(PolicyClause.policy_id == policy.id).delete()
    db.query(PolicyField).filter(PolicyField.policy_id == policy.id).delete()
    db.commit()

    clause_extractor.analyze_and_populate_policy(db, policy.id)
    db.refresh(policy)
    return {"message": "Policy re-analysed successfully.", "status": policy.extraction_status}

@router.put("/{policy_id}/clauses/{clause_id}", response_model=PolicyClauseSchema)
def update_clause(
    policy_id: str,
    clause_id: str,
    req: ClauseUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    policy = db.query(Policy).filter(Policy.id == policy_id, Policy.user_id == current_user.id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy document not found.")

    clause = db.query(PolicyClause).filter(PolicyClause.id == clause_id, PolicyClause.policy_id == policy_id).first()
    if not clause:
        raise HTTPException(status_code=404, detail="Clause not found.")

    if req.heading is not None:
        clause.heading = req.heading
    if req.verbatim_text is not None:
        clause.verbatim_text = req.verbatim_text
    if req.plain_summary is not None:
        clause.plain_summary = req.plain_summary
    if req.extraction_status is not None:
        clause.extraction_status = req.extraction_status

    db.commit()
    db.refresh(clause)
    return clause

@router.get("/{policy_id}/pages/{page_number}", response_model=PolicyPageSchema)
def get_page(policy_id: str, page_number: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    policy = db.query(Policy).filter(Policy.id == policy_id, Policy.user_id == current_user.id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy document not found.")

    page = db.query(PolicyPage).filter(PolicyPage.policy_id == policy_id, PolicyPage.page_number == page_number).first()
    if not page:
        raise HTTPException(status_code=404, detail=f"Page {page_number} not found.")
    return page

@router.post("/seed-demo")
def seed_demo_policies(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Seeds the two synthetic demo policies into the user's account for immediate evaluation"""
    demo_dir = os.path.join(BACKEND_DIR, "data", "demo_policies")
    demo_files = [
        ("PolicyLens_CareSecure_Direct.pdf", "CareSecure Direct Health Insurance"),
        ("PolicyLens_HealthProtect_CanaraBank.pdf", "Canara HealthProtect Bancassurance Scheme")
    ]

    seeded = []
    user_upload_dir = os.path.join(UPLOADS_DIR, current_user.id)
    os.makedirs(user_upload_dir, exist_ok=True)

    for fn, prod_title in demo_files:
        src = os.path.join(demo_dir, fn)
        if not os.path.exists(src):
            continue

        file_id = str(uuid.uuid4())
        dest_filename = f"{file_id}.pdf"
        dest_path = os.path.join(user_upload_dir, dest_filename)
        shutil.copyfile(src, dest_path)

        file_hash = pdf_service.calculate_file_hash(dest_path)
        rel_path = os.path.relpath(dest_path, BACKEND_DIR)

        # Check if already seeded
        existing = db.query(Policy).filter(Policy.user_id == current_user.id, Policy.file_hash == file_hash).first()
        if existing:
            seeded.append(existing.product_name)
            continue

        policy = Policy(
            id=file_id,
            user_id=current_user.id,
            original_filename=fn,
            stored_relative_path=rel_path,
            file_hash=file_hash,
            extraction_status="Analysed",
            is_demo=True
        )
        db.add(policy)
        db.commit()

        # Extract and index
        extraction_result = pdf_service.extract_document(dest_path)
        policy.page_count = extraction_result["page_count"]
        policy.ocr_used = extraction_result["ocr_used"]
        policy.ocr_confidence_avg = extraction_result["ocr_confidence_avg"]

        pages_data = []
        for p in extraction_result["pages"]:
            page_obj = PolicyPage(
                policy_id=policy.id,
                page_number=p["page_number"],
                extracted_text=p["text"],
                extraction_method=p["extraction_method"],
                ocr_confidence=p["ocr_confidence"],
                has_tables=p["has_tables"],
                needs_review=p["needs_review"]
            )
            db.add(page_obj)
            pages_data.append(p)
        db.commit()

        retrieval_service.index_policy_pages(db, policy.id, pages_data)
        clause_extractor.analyze_and_populate_policy(db, policy.id)
        db.refresh(policy)
        seeded.append(policy.product_name)

    return {"message": "Demo policies seeded successfully.", "policies": seeded}
