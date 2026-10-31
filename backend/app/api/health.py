from fastapi import APIRouter
from app.services.gemini_service import gemini_service
from app.services.ocr_service import ocr_service
from app.schemas.schemas import AIHealthResponse

router = APIRouter(prefix="/api/health", tags=["Health & Status"])

@router.get("")
def health_check():
    return {
        "status": "healthy",
        "service": "PolicyLens Backend",
        "version": "1.0.0-prototype",
        "platform": "Windows Local-First"
    }

@router.get("/ai", response_model=AIHealthResponse)
def get_ai_status():
    """Returns whether Gemini API is configured without revealing keys"""
    return gemini_service.get_status()

@router.get("/ocr")
def get_ocr_status():
    """Returns local OCR engine detection status"""
    return ocr_service.get_status()
