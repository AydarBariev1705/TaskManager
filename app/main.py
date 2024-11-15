from fastapi import FastAPI
from app.task_router import task_router
from app.user_router import user_router
from app.database import init_db

app = FastAPI()
app.include_router(task_router)
app.include_router(user_router)
@app.on_event("startup")
async def on_startup():
    await init_db()