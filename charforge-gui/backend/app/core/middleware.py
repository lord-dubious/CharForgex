"""Middleware for optional authentication."""

from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional

from app.core.config import settings
from app.core.database import SessionLocal, User
from app.core.auth import get_current_user_from_token

security = HTTPBearer(auto_error=False)

async def get_current_user_middleware(request: Request) -> User:
    """Middleware to get current user with optional authentication."""
    
    if not settings.ENABLE_AUTH:
        # When auth is disabled, return default user
        db = SessionLocal()
        try:
            return await get_or_create_default_user(db)
        finally:
            db.close()
    
    # When auth is enabled, extract token from request
    authorization: Optional[HTTPAuthorizationCredentials] = await security(request)
    
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    db = SessionLocal()
    try:
        user = await get_current_user_from_token(authorization.credentials, db)
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        return user
    finally:
        db.close()

async def get_or_create_default_user(db: Session) -> User:
    """Get or create default user in a thread-safe manner."""
    
    # Try to get existing default user
    default_user = db.query(User).filter(User.id == settings.DEFAULT_USER_ID).first()
    if default_user:
        return default_user
    
    # Create default user if it doesn't exist
    try:
        default_user = User(
            id=settings.DEFAULT_USER_ID,
            username="default_user",
            email="default@charforge.local",
            hashed_password="",  # No password needed when auth is disabled
            is_active=True
        )
        db.add(default_user)
        db.commit()
        db.refresh(default_user)
        return default_user
    except IntegrityError:
        # Another request created the user, rollback and fetch it
        db.rollback()
        default_user = db.query(User).filter(User.id == settings.DEFAULT_USER_ID).first()
        if not default_user:
            # This should not happen, but handle it gracefully
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create or retrieve default user"
            )
        return default_user

class OptionalAuthMiddleware:
    """Middleware class for optional authentication."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            
            # Skip auth for certain paths
            skip_paths = ["/docs", "/redoc", "/openapi.json", "/api/auth/config"]
            if any(request.url.path.startswith(path) for path in skip_paths):
                await self.app(scope, receive, send)
                return
            
            # Add user to request state if needed
            if not settings.ENABLE_AUTH:
                db = SessionLocal()
                try:
                    user = await get_or_create_default_user(db)
                    scope["state"] = {"user": user}
                finally:
                    db.close()
        
        await self.app(scope, receive, send)
