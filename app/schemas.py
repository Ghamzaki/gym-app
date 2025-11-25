# app/schemas.py
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Literal

# --- ROLE DEFINITION ---
UserRole = Literal["admin", "member", "trainer"]

# --- USER SCHEMAS ---
class UserBase(BaseModel):
    email: EmailStr
    name: str
    role: UserRole = "member"

class UserCreate(UserBase):
    password: str

class UserUpdateRole(BaseModel):
    role: UserRole

class UserPublic(UserBase):
    id: int

    #class Config:
        #from_attributes = True
    model_config = ConfigDict(from_attributes=True)

# --- AUTHENTICATION SCHEMAS ---
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    email: str | None = None
    roles: list[UserRole] = []

# --- CLASS SCHEMAS ---
class ClassBase(BaseModel):
    name: str
    trainer_id: int 
    max_capacity: int
    duration_minutes: int = 60 

class ClassCreate(ClassBase):
    pass

class ClassPublic(ClassBase):
    id: int

    class Config:
        from_attributes = True

# --- BOOKING SCHEMAS ---
class BookingBase(BaseModel):
    class_id: int
    member_id: int 

class BookingCreate(BookingBase):
    pass

class BookingPublic(BookingBase):
    id: int

    class Config:
        from_attributes = True