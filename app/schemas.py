from pydantic import BaseModel
from app.enums import TaskStatus

class UserCreate(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TaskCreate(BaseModel):
    title: str
    description: str
    status: TaskStatus

class TaskOut(BaseModel):
    id: int
    title: str
    description: str
    status: TaskStatus

class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: TaskStatus | None = None
