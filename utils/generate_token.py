from datetime import datetime, timedelta
from jose import jwt
from fastapi import Response
from config.settings import settings


def create_access_token(user_id: str) -> str:
    """Create JWT access token"""
    expire = datetime.utcnow() + timedelta(days=settings.JWT_EXPIRE_DAYS)
    to_encode = {
        "userId": str(user_id),
        "exp": expire
    }
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET, 
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def generate_token(response: Response, user_id: str):
    """Generate JWT and set it as HTTP-only cookie"""
    token = create_access_token(user_id)
    
    # Set cookie with same settings as Node.js version
    response.set_cookie(
        key="jwt",
        value=token,
        httponly=True,
        secure=settings.NODE_ENV != "development",  # True in production
        samesite="lax" if settings.NODE_ENV == "development" else "strict",  # Lax in dev for cross-origin
        max_age=settings.JWT_EXPIRE_DAYS * 24 * 60 * 60,  # 30 days in seconds
        path="/",  # Available on all routes
    )
