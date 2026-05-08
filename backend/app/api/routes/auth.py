from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.deps import get_current_user, get_db
from app.core.config import settings
from app.schemas.auth import UserCreate, UserLogin, UserResponse, TokenResponse, RefreshRequest
from app.services import auth_service
from app.models.user import User

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.RATE_LIMIT_LOGIN)
async def register(request: Request, body: UserCreate, db: AsyncSession = Depends(get_db)):
    user = await auth_service.register_user(db, body)
    return await auth_service.create_tokens(db, user)


@router.post("/login", response_model=TokenResponse)
@limiter.limit(settings.RATE_LIMIT_LOGIN)
async def login(request: Request, credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    user = await auth_service.authenticate_user(db, credentials)
    return await auth_service.create_tokens(db, user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: RefreshRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.refresh_tokens(db, request.refresh_token)


@router.post("/logout")
async def logout(request: RefreshRequest, db: AsyncSession = Depends(get_db)):
    await auth_service.revoke_refresh_token(db, request.refresh_token)
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_me(data: UserCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    current_user.username = data.username
    current_user.email = data.email
    if data.password:
        from app.core.security import hash_password
        current_user.hashed_password = hash_password(data.password)
    await db.flush()
    await db.refresh(current_user)
    return current_user
