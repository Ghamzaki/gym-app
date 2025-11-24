# app/schemas.py
from pydantic import BaseModel, EmailStr
from typing import Literal

UserRole = Literal["admin", "trainer", "member"]

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

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    email: str | None = None
    roles: list[UserRole] = []