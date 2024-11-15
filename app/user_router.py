from fastapi import APIRouter, Depends, HTTPException, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import UserCreate, Token, UserOut
from app.database import get_db
from app.auth import authenticate_user, create_access_token, create_refresh_token,register_user, delete_tokens, get_username_from_token, set_tokens_in_redis
from app.task_redis import get_redis
import redis.asyncio as aioredis

user_router = APIRouter()

@user_router.post("/auth/register", response_model=UserOut)
async def register(
    user: UserCreate, db: AsyncSession = Depends(get_db),
    ):

    new_user = await register_user(db, user)
    return new_user

@user_router.post("/auth/login", response_model=Token)
async def login(
    user: UserCreate, response: Response, 
    redis: aioredis.Redis = Depends(get_redis), db: AsyncSession = Depends(get_db),
    ):

    db_user = await authenticate_user(
        db=db, 
        username=user.username, 
        password=user.password,
        )
    if not db_user:
        raise HTTPException(
            status_code=400, 
            detail="Incorrect username or password",
            )
    
    access_token = create_access_token(
        {"sub": db_user.username},
        )
    refresh_token = create_refresh_token(
        {"sub": db_user.username},
        )
    tokens = await set_tokens_in_redis(
        username=db_user.username,
        redis=redis, 
        access_token=access_token, 
        refresh_token=refresh_token,
        )
    response.set_cookie(
        key="refresh_token", 
        value=refresh_token,
        )
    response.set_cookie(
        key="access_token", 
        value=access_token,
        )

    return tokens

@user_router.post("/auth/logout")
async def logout(request: Request, response: Response, redis: aioredis.Redis = Depends(get_redis), db: AsyncSession = Depends(get_db), ):
    return await delete_tokens(
        request=request, 
        response=response,
        db=db, 
        redis=redis, 
        )
@user_router.post("/auth/refresh")
async def refresh(request: Request, redis: aioredis.Redis = Depends(get_redis), db: AsyncSession = Depends(get_db), ):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=401, 
            detail="Refresh token not found!")
    username = await get_username_from_token(refresh_token)
    new_access_token = create_access_token(
        {"sub": username},
        )
    tokens = await set_tokens_in_redis(
        username=username,
        redis=redis, 
        access_token=new_access_token, 
        refresh_token=refresh_token,
        )
    
    return {"message": "Refreshed successfully", "tokens": tokens}
    