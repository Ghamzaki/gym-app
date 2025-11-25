# app/crud.py
from sqlalchemy.orm import Session
from . import models, schemas
from .auth import get_password_hash

# --- USER CRUD OPERATIONS ---

def get_user_by_email(db: Session, email: str):
    """Retrieves a user object by their email address."""
    return db.query(models.DBUser).filter(models.DBUser.email == email).first()

def get_user_by_id(db: Session, user_id: int):
    """Retrieves a user object by their primary key ID."""
    return db.query(models.DBUser).filter(models.DBUser.id == user_id).first()

def create_user(db: Session, user: schemas.UserCreate):
    """Creates a new user, automatically hashing the password and setting the role to 'member'."""
    # Note: role is fixed to 'member' on public registration
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
    """Updates the role of a user (Admin-only access required)."""
    db_user = get_user_by_id(db, user_id)
    if db_user:
        db_user.role = role
        db.commit()
        db.refresh(db_user)
    return db_user

# --- CLASS CRUD OPERATIONS (Trainer/Admin Management) ---

def create_class(db: Session, gym_class: schemas.ClassCreate):
    """Creates a new gym class template."""
    # Note: model_dump() safely converts the Pydantic model to a dict for the SQLAlchemy model
    db_class = models.DBClass(**gym_class.model_dump())
    db.add(db_class)
    db.commit()
    db.refresh(db_class)
    return db_class

def get_classes(db: Session, skip: int = 0, limit: int = 100):
    """Retrieves a list of all available gym classes."""
    return db.query(models.DBClass).offset(skip).limit(limit).all()

def get_class_by_id(db: Session, class_id: int):
    """Retrieves a single class by its ID."""
    return db.query(models.DBClass).filter(models.DBClass.id == class_id).first()

# --- BOOKING CRUD OPERATIONS (Member/User Actions) ---

def create_booking(db: Session, class_id: int, member_id: int):
    """
    Creates a booking for a user in a specific class, enforcing capacity limits.
    Returns: DBBooking object on success, "Capacity Full" string on failure, or None if class not found.
    """
    # 1. Check if the class exists
    gym_class = get_class_by_id(db, class_id)
    if not gym_class:
        return None
    
    # 2. Check current capacity
    current_bookings = db.query(models.DBBooking).filter(models.DBBooking.class_id == class_id).count()
    
    if current_bookings >= gym_class.max_capacity:
        return "Capacity Full" 

    # 3. Create the booking
    db_booking = models.DBBooking(class_id=class_id, member_id=member_id)
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    return db_booking

def get_bookings_by_member(db: Session, member_id: int):
    """Retrieves all class bookings made by a specific user."""
    return db.query(models.DBBooking).filter(models.DBBooking.member_id == member_id).all()