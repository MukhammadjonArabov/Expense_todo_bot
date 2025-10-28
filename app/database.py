import os
import enum
import uuid
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy import (
    Column, Integer, String, BigInteger, Boolean, ForeignKey,
    DateTime, Text, Enum, func, Date,
)

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL .env not found!")

Base = declarative_base()

engine = create_async_engine(
    DATABASE_URL,
    echo=True
)

async_session = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


# ============================
# MODELS
# ============================

class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String, nullable=True)
    user_link = Column(String, nullable=True)
    phone = Column(String, nullable=False)

    projects_created = relationship(
        "Project",
        back_populates="creator",
        cascade="all, delete-orphan"
    )

    tasks_assigned = relationship(
        "Task",
        back_populates="assigned_user",
        foreign_keys="[Task.assigned_to]"
    )

    tasks_created = relationship(
        "Task",
        back_populates="creator_user",
        foreign_keys="[Task.user_id]"
    )

    personal_tasks = relationship(
        "PersonalTask",
        back_populates="user",
        cascade="all, delete-orphan"
    )


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Integer, nullable=False)
    reason = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class RoleEnum(enum.Enum):
    admin = "admin"
    owner = "owner"
    member = "member"
    viewer = "viewer"


class Project(Base):
    __tablename__ = "projects"

    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String(155), nullable=False)
    description = Column(Text, nullable=True)
    create_by = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    create_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    invite_token = Column(String(255), unique=True, nullable=False, default=lambda: uuid.uuid4().hex)
    invite_link = Column(String(500), nullable=True)

    creator = relationship("User", back_populates="projects_created")
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")


class ProjectMember(Base):
    __tablename__ = "project_members"

    id = Column(BigInteger, primary_key=True, index=True)
    project_id = Column(BigInteger, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(Enum(RoleEnum), default=RoleEnum.member, nullable=False)
    joined_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    project = relationship("Project", back_populates="members")
    user = relationship("User")


class TaskStatusEnum(enum.Enum):
    new = "new"
    in_progress = "in_progress"
    done = "done"
    blocked = "blocked"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(BigInteger, primary_key=True, index=True)
    title = Column(String, nullable=False)
    status = Column(Enum(TaskStatusEnum), default=TaskStatusEnum.new, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deadline = Column(DateTime(timezone=True), nullable=False)
    is_done = Column(Boolean, default=False, nullable=False)

    project_id = Column(BigInteger, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    assigned_to = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    project = relationship("Project", back_populates="tasks")

    creator_user = relationship(
        "User",
        back_populates="tasks_created",
        foreign_keys=[user_id]
    )

    assigned_user = relationship(
        "User",
        back_populates="tasks_assigned",
        foreign_keys=[assigned_to]
    )

class PersonalTask(Base):
    __tablename__ = "personal_tasks"

    id = Column(BigInteger, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    deadline = Column(Date, nullable=False)
    is_completed = Column(Integer, default=0)

    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="personal_tasks")

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Jadval(lar) yaratildi.")
