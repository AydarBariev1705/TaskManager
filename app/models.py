from sqlalchemy import Column, Integer, String, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.database import Base
from app.enums import TaskStatus

class User(Base):
    __tablename__ = "users"
    id = Column(
        Integer, primary_key=True, index=True,
        )
    username = Column(
        String, unique=True, index=True,
        )
    password_hash = Column(String)

class Task(Base):
    __tablename__ = "tasks"
    id = Column(
        Integer, primary_key=True, index=True,
        )
    title = Column(
        String, index=True,
        )
    description = Column(
        String, index=True,
        )
    status = Column(
        Enum(TaskStatus), 
        default=TaskStatus.IN_PROGRESS,
        )
    user_id = Column(
        Integer, ForeignKey("users.id"),
        )
    user = relationship("User")
