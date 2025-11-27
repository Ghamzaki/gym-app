# app/main.py
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated


# Absolute imports work because Uvicorn is run from the project root
from . import models, schemas, crud, auth
from .database import engine, get_db
from .dependencies import (
    CURRENT_USER_DEPENDENCY, ADMIN_ONLY, TRAINER_OR_ADMIN, DB_DEPENDENCY
)

# Initialize the database and create tables on startup
# This command connects to Supabase/PostgreSQL and ensures the tables exist.
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="A RBAC Gym API",
    description="JWT Authentication and Role-Based Access Control using Python/FastAPI and PostgreSQL.",
)

# --- USER AUTHENTICATION & PROFILE ROUTES ---

@app.post("/register", response_model=schemas.UserPublic, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: schemas.UserCreate, db: DB_DEPENDENCY):
    """Register a new user with the default 'member' role."""
    db_user = crud.get_user_by_email(db, email=user_data.email)
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    new_user = crud.create_user(db, user=user_data)
    return schemas.UserPublic.model_validate(new_user)

@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: DB_DEPENDENCY):
    """Generates an access token upon successful login."""
    user = crud.get_user_by_email(db, email=form_data.username)
    
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create the JWT payload, including the user's single role
    access_token = auth.create_access_token(
        data={"sub": user.email, "roles": [user.role]},
        expires_delta=auth.timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=schemas.UserPublic)
async def read_users_me(current_user: CURRENT_USER_DEPENDENCY):
    """Returns the profile of the current authenticated user."""
    return current_user

# --- ROLE-BASED ACCESS CONTROL (RBAC) EXAMPLES ---

@app.get("/services", response_model=list[str], dependencies=[Depends(CURRENT_USER_DEPENDENCY)])
async def get_services(current_user: CURRENT_USER_DEPENDENCY):
    """Retrieves a list of available gym services accessible by any logged-in user."""
    
    # List of available services
    available_services = [
        "Cardio Area Access",
        "Strength Training Zone",
        "Group Fitness Classes (Premium)",
        "Personal Training Sessions (Bookable)",
        "Locker Room Access"
    ]
    return available_services

@app.get("/trainer-data", response_model=str, dependencies=[Depends(TRAINER_OR_ADMIN)])
async def get_trainer_data():
    """Access granted only to users with 'admin' or 'trainer' roles."""
    return "Access to trainer-specific schedules and client notes."

@app.patch("/admin/update-role/{user_id}", response_model=schemas.UserPublic, dependencies=[Depends(ADMIN_ONLY)])
async def update_user_role(
    user_id: int, 
    role_update: schemas.UserUpdateRole, 
    db: DB_DEPENDENCY
):
    """Access granted only to users with the 'admin' role to change another user's role."""
    db_user = crud.update_user_role(db, user_id=user_id, role=role_update.role)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
    return schemas.UserPublic.model_validate(db_user)

# --- CLASS MANAGEMENT ROUTES ---

@app.post("/classes", response_model=schemas.ClassPublic, status_code=status.HTTP_201_CREATED, dependencies=[Depends(TRAINER_OR_ADMIN)])
async def create_new_class(class_data: schemas.ClassCreate, db: DB_DEPENDENCY):
    """Allows Trainers and Admins to create new class templates."""
    # TODO: Optional: Validate that class_data.trainer_id exists and is actually a 'trainer'
    return crud.create_class(db, gym_class=class_data)

@app.get("/classes", response_model=list[schemas.ClassPublic])
async def list_classes(db: DB_DEPENDENCY, skip: int = 0, limit: int = 100):
    """Lists all available classes (accessible to anyone, including unauthenticated users if you removed the dependency from the file)."""
    return crud.get_classes(db, skip=skip, limit=limit)


# --- BOOKING ROUTES ---

@app.post("/bookings", response_model=schemas.BookingPublic, status_code=status.HTTP_201_CREATED)
async def book_class(
    booking_data: schemas.BookingCreate, 
    current_user: CURRENT_USER_DEPENDENCY,
    db: DB_DEPENDENCY
):
    """Allows any logged-in user (Member, Trainer, or Admin) to book a class."""
    
    # 1. Enforce that the user books for themselves
    if booking_data.member_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot book for another user.")
    
    # We use current_user.id for the member_id in the booking
    result = crud.create_booking(db, 
                                 class_id=booking_data.class_id, 
                                 member_id=current_user.id) 

    if result == "Capacity Full":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Class is fully booked.")
    
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found.")

    return result

@app.get("/users/me/bookings", response_model=list[schemas.BookingPublic])
async def get_my_bookings(current_user: CURRENT_USER_DEPENDENCY, db: DB_DEPENDENCY):
    """Returns all bookings made by the current user."""
    return crud.get_bookings_by_member(db, member_id=current_user.id)