import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BACKEND_DIR, ".env"))

from app.database import init_db, SessionLocal
from app.models.models import User
from app.api.deps import hash_password
from app.api import auth, policies, comparisons, scenarios, chat, hospitals, health

@asynccontextmanager
async def lifespan(app: FastAPI):
    # On Startup:
    init_db()
    # Seed default demo user if not present
    db = SessionLocal()
    try:
        demo_user = db.query(User).filter(User.email == "judge.demo@policylens.local").first()
        if not demo_user:
            demo_user = User(
                email="judge.demo@policylens.local",
                password_hash=hash_password("DemoJudge2026!"),
                name="Hackathon Judge Demo",
                is_demo=True,
                gemini_consent=True
            )
            db.add(demo_user)
            db.commit()
    except Exception as e:
        print(f"Startup seed notice: {e}")
    finally:
        db.close()
    yield
    # On Shutdown:
    pass

app = FastAPI(
    title="PolicyLens API",
    description="Intelligent Insurance Policy Understanding & Risk Navigator",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for local Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth.router)
app.include_router(policies.router)
app.include_router(comparisons.router)
app.include_router(scenarios.router)
app.include_router(chat.router)
app.include_router(hospitals.router)
app.include_router(health.router)

@app.get("/")
def root():
    return {
        "app": "PolicyLens",
        "purpose": "Intelligent Insurance Policy Understanding & Risk Navigator",
        "status": "Online",
        "docs_url": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8001))
    uvicorn.run("app.main:app", host="127.0.0.1", port=port, reload=True)
