from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext
from database.schemas import UserRegisterRequest, UserResponse
from database.crud import create_user, get_user_by_email

# Import routers
from app.api import health, jobs, auth

app = FastAPI(
    title="Multi-Agent Research Assistant API",
    description="Research assistant using CrewAI, Groq LLMs, and FastAPI",
    version="1.0.0"
)

# ──────────────────────────────────────────────
# CORS Configuration
# ──────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────────
# Password Hashing Setup
# ──────────────────────────────────────────────
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """Hash a password using pbkdf2_sha256."""
    return pwd_context.hash(password)

# ──────────────────────────────────────────────
# Include Routers
# ──────────────────────────────────────────────
app.include_router(health.router)
app.include_router(jobs.router)
app.include_router(auth.router)

# ──────────────────────────────────────────────
# User Authentication Endpoints
# ──────────────────────────────────────────────

@app.post("/users/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: UserRegisterRequest):
    """
    Register a new user to the system.
    """
    # Check if user already exists
    existing_user = get_user_by_email(user.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Hash password
    hashed_password = get_password_hash(user.password)
    
    # Create the user in the DB
    try:
        new_user = create_user(
            email=user.email,
            username=user.username,
            password_hash=hashed_password
        )
        return new_user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.get("/")
def read_root():
    return {
        "message": "Welcome to the Multi-Agent Research Assistant API",
        "docs": "http://127.0.0.1:8000/docs",
        "health": "http://127.0.0.1:8000/health"
    }

