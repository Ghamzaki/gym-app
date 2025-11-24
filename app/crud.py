# app/crud.py
from sqlalchemy.orm import Session
from . import models, schemas
from .auth import get_password_hash

def get_user_by_email(db: Session, email: str):
    return db.query(models.DBUser).filter(models.DBUser.email == email).first()

def get_user_by_id(db: Session, user_id: int):
    return db.query(models.DBUser).filter(models.DBUser.id == user_id).first()

def create_user(db: Session, user: schemas.UserCreate):
    # Note: role is fixed to 'member' unless manually set later by an admin
    hashed_password = get_password_hash(user.password)
    db_user = models.DBUser(
        email=user.email,
        name=user.name,
        role="member", # Enforce 'member' on public registration
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user_role(db: Session, user_id: int, role: schemas.UserRole):
    db_user = get_user_by_id(db, user_id)
    if db_user:
        db_user.role = role
        db.commit()
        db.refresh(db_user)
    return db_user