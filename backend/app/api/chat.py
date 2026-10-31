import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import User, ChatSession, ChatMessage
from app.schemas.schemas import ChatMessageRequest, ChatMessageResponse, ChatSessionResponse
from app.api.deps import get_current_user
from app.services.agent_service import agent_service

router = APIRouter(prefix="/api/chat", tags=["Chat"])

@router.post("", response_model=ChatMessageResponse)
def send_chat_message(
    req: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        res = agent_service.process_chat_message(
            db=db,
            user_id=current_user.id,
            message=req.message,
            session_id=req.session_id,
            policy_id=req.policy_id,
            user_consented=current_user.gemini_consent
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat processing error: {str(e)}")

@router.get("/sessions", response_model=List[ChatSessionResponse])
def list_sessions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    sessions = db.query(ChatSession).filter(ChatSession.user_id == current_user.id).order_by(ChatSession.created_at.desc()).all()
    results = []
    for s in sessions:
        results.append({
            "id": s.id,
            "title": s.title,
            "policy_id": s.policy_id,
            "created_at": s.created_at,
            "messages": []
        })
    return results

@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found.")

    formatted_messages = []
    for m in session.messages:
        sources = []
        try:
            sources = json.loads(m.sources_json) if m.sources_json else []
        except Exception:
            sources = []

        formatted_messages.append({
            "id": m.id,
            "session_id": m.session_id,
            "role": m.role,
            "message_text": m.message_text,
            "sources": sources,
            "created_at": m.created_at
        })

    return {
        "id": session.id,
        "title": session.title,
        "policy_id": session.policy_id,
        "created_at": session.created_at,
        "messages": formatted_messages
    }
