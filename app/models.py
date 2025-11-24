# app/models.py
from sqlalchemy import Boolean, Column, Integer, String
from .database import Base

class DBUser(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="member") # admin, trainer, member
    is_active = Column(Boolean, default=True)