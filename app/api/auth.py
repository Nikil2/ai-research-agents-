"""Login/Authentication endpoints for user credential verification."""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from passlib.context import CryptContext
from database.crud import get_user_by_email

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Password hashing setup
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    user_id: str
    email: str
    username: str
    message: str

@router.post("/login", response_model=LoginResponse)
def login(credentials: LoginRequest):
    """
    Login with email and password.
    Returns user_id if credentials are valid.
    """
    user = get_user_by_email(credentials.email)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not pwd_context.verify(credentials.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    return LoginResponse(
        user_id=str(user["id"]),
        email=user["email"],
        username=user["username"],
        message="Login successful"
    )
