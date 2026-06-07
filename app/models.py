from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    display_name = Column(String(50), nullable=False)
    color = Column(String(7), default="#4f46e5")
    role = Column(String(20), default="member")  # admin, member
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    entries = relationship("Entry", back_populates="user")
    invitations = relationship("Invitation", back_populates="created_by")
    suggested_tasks = relationship("Task", back_populates="suggested_by_user")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    points = Column(Integer, default=1)
    icon = Column(String(10), default="🏠")
    active = Column(Boolean, default=True)
    status = Column(String(20), default="approved")  # approved, pending, rejected
    suggested_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    suggested_by_user = relationship("User", back_populates="suggested_tasks")
    entries = relationship("Entry", back_populates="task")


class Entry(Base):
    __tablename__ = "entries"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    points = Column(Integer, nullable=False)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    month = Column(String(7), nullable=False)  # YYYY-MM

    user = relationship("User", back_populates="entries")
    task = relationship("Task", back_populates="entries")


class Invitation(Base):
    __tablename__ = "invitations"

    id = Column(Integer, primary_key=True)
    token = Column(String(64), unique=True, nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    used = Column(Boolean, default=False)
    used_by = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)

    created_by = relationship("User", back_populates="invitations")
