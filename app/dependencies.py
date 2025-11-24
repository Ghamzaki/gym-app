# app/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Annotated

from . import schemas, crud
from .database import get_db
from .auth import SECRET_KEY, ALGORITHM, jwt, JWTError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

DB_DEPENDENCY = Annotated[Session, Depends(get_db)]

async def get_current_user(
    db: DB_DEPENDENCY,
    token: Annotated[str, Depends(oauth2_scheme)]
) -> schemas.UserPublic:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        roles_list: list[schemas.UserRole] = payload.get("roles", []) 
        
        if email is None or not roles_list:
            raise credentials_exception
        
        # token_data = schemas.TokenData(email=email, roles=roles_list) # Not strictly needed
    except JWTError:
        raise credentials_exception

    db_user = crud.get_user_by_email(db, email=email)
    if db_user is None:
        raise credentials_exception
    
    return schemas.UserPublic.model_validate(db_user)


def role_checker(required_roles: list[schemas.UserRole]):
    def wrapper(current_user: Annotated[schemas.UserPublic, Depends(get_current_user)]):
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions. Required roles: {', '.join(required_roles)}",
            )
        return current_user
    return wrapper

# Pre-defined dependencies
ADMIN_ONLY = role_checker(["admin"])
TRAINER_OR_ADMIN = role_checker(["admin", "trainer"])
CURRENT_USER_DEPENDENCY = Annotated[schemas.UserPublic, Depends(get_current_user)]