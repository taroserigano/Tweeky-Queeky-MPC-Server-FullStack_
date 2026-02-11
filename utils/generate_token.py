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
    # Use 'lax' samesite for cross-origin support (ECS Fargate has different IPs)
    response.set_cookie(
        key="jwt",
        value=token,
        httponly=True,
        secure=False,  # Set to False for HTTP (ECS without ALB/HTTPS)
        samesite="lax",  # Allow cross-site GET requests (needed for different IPs)
        max_age=settings.JWT_EXPIRE_DAYS * 24 * 60 * 60,  # 30 days in seconds
        path="/",  # Available on all routes
    )
