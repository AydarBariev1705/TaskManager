from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import Task
from app.schemas import TaskCreate, TaskUpdate
from fastapi import HTTPException

async def get_tasks(
        db: AsyncSession, user_id: int, status: str = None,
        ):
    query = select(Task).filter(Task.user_id == user_id)
    if status:
        query = query.filter(Task.status == status)
    tasks = await db.execute(query)
    return tasks.scalars().all()

async def get_task(
        db: AsyncSession, user_id: int, task_id: int, status: str = None):
    query = select(Task).filter(Task.user_id == user_id, Task.id == task_id)
    task = await db.execute(query)
    return task.scalars().first()

async def create_task(
        db: AsyncSession, task: TaskCreate, user_id: int,
        ):
    db_task = Task(**task.dict(), user_id=user_id)
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)
    return db_task

async def update_task(
        db: AsyncSession, task_id: int, task: TaskUpdate, user_id: int,
        ):
    db_task = await db.get(Task, task_id)
    if not db_task or db_task.user_id != user_id:
        raise HTTPException(
            status_code=404, 
            detail="Task not found",
            )
    for key, value in task.dict(exclude_unset=True).items():
        setattr(db_task, key, value)
    await db.commit()
    await db.refresh(db_task)
    return db_task

async def delete_task(
        db: AsyncSession, task_id: int, user_id: int,
        ):
    db_task = await db.get(Task, task_id)
    if not db_task or db_task.user_id != user_id:
        raise HTTPException(
            status_code=404, 
            detail="Task not found",
            )
    await db.delete(db_task)
    await db.commit()
    return db_task
