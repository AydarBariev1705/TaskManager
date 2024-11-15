from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import TaskCreate, TaskUpdate, TaskOut
from app.database import get_db
from app.auth import get_current_user, get_token_from_cookies
from app.crud import create_task, get_tasks, delete_task, update_task, get_task
from app.task_redis import get_redis
import redis.asyncio as aioredis

task_router = APIRouter()

@task_router.post("/tasks", response_model=TaskOut)
async def create_task_endpoint(
    task: TaskCreate, 
    request: Request, 
    db: AsyncSession = Depends(get_db), 
    redis: aioredis.Redis = Depends(get_redis),
    ):

    access_token, refresh_token = await get_token_from_cookies(
        request=request,
        )
    current_user = await get_current_user(
        request=request, 
        db=db, 
        redis=redis, 
        access_token=access_token, 
        refresh_token=refresh_token,
        )
    new_task = await create_task(
        db=db, 
        task=task, 
        user_id=current_user.id,
        )
    return new_task

@task_router.get("/tasks", response_model=list[TaskOut])
async def get_tasks_endpoint(
    request: Request, 
    db: AsyncSession = Depends(get_db), 
    redis: aioredis.Redis = Depends(get_redis),
    status: str = None,
    ):

    access_token, refresh_token = await get_token_from_cookies(
        request=request,
        )
    current_user = await get_current_user(
        request=request, 
        db=db, 
        redis=redis, 
        access_token=access_token, 
        refresh_token=refresh_token,
        )
    tasks = await get_tasks(
        db=db, 
        user_id=current_user.id, 
        status=status, 
        )
    return tasks

@task_router.get("/tasks/{task_id}", response_model=TaskOut)
async def get_task_endpoint(
    task_id: int, 
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    ):

    access_token, refresh_token = await get_token_from_cookies(
        request=request,
        )
    current_user = await get_current_user(
        request=request, 
        db=db, 
        redis=redis, 
        access_token=access_token, 
        refresh_token=refresh_token,
        )
    db_task = await get_task(
        db=db, 
        task_id=task_id, 
        user_id=current_user.id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    return db_task


@task_router.put("/tasks/{task_id}", response_model=TaskUpdate)
async def update_task_endpoint(
    task_id: int, 
    task: TaskUpdate, request: Request,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    ):

    access_token, refresh_token = await get_token_from_cookies(
        request=request,
        )
    current_user = await get_current_user(
        request=request, 
        db=db, 
        redis=redis, 
        access_token=access_token, 
        refresh_token=refresh_token,
        )
    db_task = await update_task(
        db=db, 
        task_id=task_id, 
        task=task, 
        user_id=current_user.id)
    return db_task

@task_router.delete("/tasks/{task_id}",)
async def delete_task_endpoint(
    task_id: int, request: Request,
    db: AsyncSession = Depends(get_db), 
    redis: aioredis.Redis = Depends(get_redis),
    ):

    access_token, refresh_token = await get_token_from_cookies(
        request=request,
        )
    current_user = await get_current_user(
        request=request, 
        db=db, 
        redis=redis, 
        access_token=access_token, 
        refresh_token=refresh_token,
        )
    db_task = await delete_task(
        db=db, 
        task_id=task_id, 
        user_id=current_user.id,
        )
    return {
        "message": f"Task {db_task.id} deleted successfully"
        }
