from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import User
from app.schemas.schemas import UserRegister, UserLogin, UserResponse, ConsentUpdate
from app.api.deps import hash_password, verify_password, create_session_token, get_current_user, ACTIVE_SESSIONS

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse)
def register(req: UserRegister, response: Response, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == req.email.lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists.")

    user = User(
        email=req.email.lower(),
        password_hash=hash_password(req.password),
        name=req.name or "Policyholder",
        is_demo=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_session_token(user.id)
    response.set_cookie(key="policylens_session", value=token, httponly=True, samesite="lax")
    return user

@router.post("/login")
def login(req: UserLogin, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email.lower()).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = create_session_token(user.id)
    response.set_cookie(key="policylens_session", value=token, httponly=True, samesite="lax")
    return {
        "token": token,
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "is_demo": user.is_demo,
            "gemini_consent": user.gemini_consent
        }
    }

@router.post("/demo-login")
def demo_login(response: Response, db: Session = Depends(get_db)):
    """One-click instant login for hackathon judges"""
    demo_email = "judge.demo@policylens.local"
    user = db.query(User).filter(User.email == demo_email).first()
    if not user:
        user = User(
            email=demo_email,
            password_hash=hash_password("DemoJudge2026!"),
            name="Hackathon Evaluator",
            is_demo=True,
            gemini_consent=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_session_token(user.id)
    response.set_cookie(key="policylens_session", value=token, httponly=True, samesite="lax")
    return {
        "token": token,
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "is_demo": user.is_demo,
            "gemini_consent": user.gemini_consent
        }
    }

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key="policylens_session")
    return {"message": "Logged out successfully"}

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/consent")
def update_gemini_consent(req: ConsentUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.gemini_consent = req.consent
    db.commit()
    return {"gemini_consent": current_user.gemini_consent}
