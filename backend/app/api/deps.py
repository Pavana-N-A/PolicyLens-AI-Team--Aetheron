import os
import hashlib
import secrets
from typing import Optional
from fastapi import Depends, HTTPException, status, Header, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import User

# In-memory active session tokens mapping token -> user_id
ACTIVE_SESSIONS = {}

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return f"{salt}:{key.hex()}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        salt, key_hex = hashed_password.split(":")
        check_key = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), 100_000)
        return secrets.compare_digest(key_hex, check_key.hex())
    except Exception:
        return False

def create_session_token(user_id: str) -> str:
    token = secrets.token_urlsafe(32)
    ACTIVE_SESSIONS[token] = user_id
    return token

def get_current_user(
    request: Request,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    # 1. Check Authorization Bearer Header
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
    
    # 2. Check Cookie fallback
    if not token:
        token = request.cookies.get("policylens_session")

    # 3. Check Demo Header fallback
    if not token and request.headers.get("x-demo-user"):
        demo_user = db.query(User).filter(User.is_demo == True).first()
        if demo_user:
            return demo_user

    if not token or token not in ACTIVE_SESSIONS:
        # Check if there is a seeded demo user for frictionless local experience
        demo_user = db.query(User).filter(User.is_demo == True).first()
        if demo_user:
            return demo_user
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please sign in or use Demo Login."
        )

    user_id = ACTIVE_SESSIONS[token]
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
