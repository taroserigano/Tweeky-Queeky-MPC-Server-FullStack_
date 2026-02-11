from fastapi import Depends, HTTPException, status, Request
from jose import JWTError, jwt
from models.user import User
from config.settings import settings
from typing import Optional


async def get_current_user(request: Request) -> User:
    """
    Dependency to get current authenticated user from JWT cookie or Authorization header
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authorized, no token",
    )
    
    # Try to get token from cookie first
    token = request.cookies.get("jwt")
    
    # If not in cookie, try Authorization header (Bearer token)
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if not token:
        raise credentials_exception
    
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: str = payload.get("userId")
        
        if user_id is None:
            raise credentials_exception
            
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authorized, token failed",
        )
    
    user = await User.get(user_id)
    
    if user is None:
        raise credentials_exception
    
    return user


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency to check if user is admin
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authorized as an admin",
        )
    return current_user


async def get_current_user_optional(request: Request) -> Optional[User]:
    """
    Dependency to get current user if authenticated, None otherwise
    """
    # Try to get token from cookie first
    token = request.cookies.get("jwt")
    
    # If not in cookie, try Authorization header
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if not token:
        return None
    
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: str = payload.get("userId")
        
        if user_id is None:
            return None
            
        user = await User.get(user_id)
        return user
        
    except JWTError:
        return None
