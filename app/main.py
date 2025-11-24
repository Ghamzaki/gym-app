# app/main.py
from fastapi import FastAPI, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from typing import Annotated

# Absolute imports work because Uvicorn is run from the project root
from . import models, schemas, crud, auth
from .database import engine, get_db
from .dependencies import (
    CURRENT_USER_DEPENDENCY, ADMIN_ONLY, TRAINER_OR_ADMIN, DB_DEPENDENCY
)

# Initialize the database and create tables on startup
# This command connects to Supabase/PostgreSQL and ensures the 'users' table exists.
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="A RBAC Gym API",
    description="JWT Authentication and Role-Based Access Control using Python/FastAPI and Render.",
)

# Serve Static Files (Frontend)
app.mount("/", StaticFiles(directory="app/static", html=True), name="static") 



## User Registration Route
@app.post("/register", response_model=schemas.UserPublic, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: schemas.UserCreate, db: DB_DEPENDENCY):
    db_user = crud.get_user_by_email(db, email=user_data.email)
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    new_user = crud.create_user(db, user=user_data)
    return schemas.UserPublic.model_validate(new_user)

## Token Generation / Login Route
@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: DB_DEPENDENCY):
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

## Protected User Profile Route
@app.get("/users/me", response_model=schemas.UserPublic)
async def read_users_me(current_user: CURRENT_USER_DEPENDENCY):
    """Returns the profile of the current authenticated user."""
    return current_user

## Role-Based Access Control (Trainer/Admin)
@app.get("/training-schedule", dependencies=[Depends(TRAINER_OR_ADMIN)])
async def get_training_schedule():
    """Access granted only to users with the 'trainer' or 'admin' role."""
    return {"message": "Access granted: This is the confidential training schedule."}

## Role-Based Access Control (Admin Only)
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