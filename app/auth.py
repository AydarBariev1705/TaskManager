from fastapi import HTTPException, status, Request, Response, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import User
from app.schemas import UserCreate
from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
import redis.asyncio as aioredis
from app.task_redis import get_redis
import json


pwd_context = CryptContext(
    schemes=["bcrypt"], deprecated="auto",
    )
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="auth/login",
    )

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(
        plain_password: str, hashed_password: str,
        ) -> bool:
    return pwd_context.verify(
        plain_password, hashed_password,
        )

async def register_user(
        db: AsyncSession, user: UserCreate,
        ):
    db_user = await db.execute(select(User).filter(User.username == user.username))
    if db_user.scalars().first():
        raise HTTPException(
            status_code=400, 
            detail="Username already registered",
            )
    
    hashed_password = hash_password(user.password)
    db_user = User(
        username=user.username, 
        password_hash=hashed_password,
        )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def authenticate_user(
        db: AsyncSession, username: str, password: str,
        ):
    result = await db.execute(select(User).where(User.username == username))
    db_user = result.scalars().first()
    if db_user and verify_password(
        password, db_user.password_hash,
        ):
        return db_user
    return None

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    to_encode.update(
        {"exp": datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_MINUTES)},
        )

    access_token = jwt.encode(
        to_encode, SECRET_KEY, algorithm=ALGORITHM,
        )
    return access_token

def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    to_encode.update(
        {"exp": datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)},
        )

    refresh_token = jwt.encode(
        to_encode, SECRET_KEY, algorithm=ALGORITHM,
        )
    return refresh_token


def verify_token(token: str):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, SECRET_KEY, algorithms=[ALGORITHM],
            )
        return payload
    except JWTError:
        raise credentials_exception


async def get_username_from_token(token: str):
    try:
        decoded_token = jwt.decode(
            token, SECRET_KEY, algorithms=[ALGORITHM],
            )
        user_id = decoded_token.get("sub")
        return user_id
    except jwt.JWTError:
        raise HTTPException(
            status_code=401, 
            detail="Invalid token",
            )
    

async def get_current_user(
        request: Request, 
        access_token: str, refresh_token: str,
        db: AsyncSession,
        redis: aioredis.Redis = Depends(get_redis),):
    
    token = request.cookies.get("refresh_token")

    try:
        decoded_token = jwt.decode(
            token, SECRET_KEY, algorithms=["HS256"],
            )
        username = decoded_token.get("sub")
        db_user = await db.execute(select(User).filter(User.username == username))        
        db_user = db_user.scalars().first()

        if db_user is None:
            raise HTTPException(
                status_code=404, 
                detail="User not found!",
                )
        tokens_json = await redis.get(db_user.username)
        if not tokens_json:
            raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            )
        tokens = json.loads(tokens_json)     
        if tokens["access_token"] != access_token or tokens["refresh_token"] != refresh_token:
            raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            )
        return db_user
    except JWTError:
        raise HTTPException(
            status_code=401, 
            detail="Invalid token!",
            )
    
async def get_token_from_cookies(request: Request):

    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=401, 
            detail="Refresh token not found!")
    
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=401, 
            detail="Access token not found!",
            )
    return access_token, refresh_token

async def delete_tokens(
        request: Request,
        response: Response,
        db: AsyncSession,
        redis: aioredis.Redis = Depends(get_redis),):
    
    access_token, refresh_token = await get_token_from_cookies(
        request=request,
        )

    try:
        decoded_token = jwt.decode(
            refresh_token, SECRET_KEY, algorithms=["HS256"],
            )
        username = decoded_token.get("sub")
        db_user = await db.execute(select(User).filter(User.username == username))        
        db_user = db_user.scalars().first()

        if db_user is None:
            raise HTTPException(
                status_code=404, 
                detail="User not found!",
                )
        await redis.delete(db_user.username)
        response.delete_cookie(key="access_token")
        response.delete_cookie(key="refresh_token")
        return {"message": "Logged out successfully"}
    except JWTError:
        raise HTTPException(
            status_code=401, 
            detail="Invalid token!",
            )

async def set_tokens_in_redis(
        username: str,
        redis: aioredis.Redis, 
        access_token: str, 
        refresh_token: str,
        ):
    tokens = {
        "access_token": access_token, 
        "refresh_token": refresh_token,
        }
    tokens_json = json.dumps(tokens)
    await redis.set(
        username, tokens_json, ex=604800,
        )
    return tokens