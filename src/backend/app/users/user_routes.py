from datetime import timedelta
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm
from app.users.user_schemas import Token, UserPublic, UserRegister
from app.config import settings
from app.users import user_crud
from app.db import database


router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)


@router.post("/login/")
def login_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(database.get_db),
) -> Token:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = user_crud.authenticate(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return Token(
        access_token=user_crud.create_access_token(
            user.id, expires_delta=access_token_expires
        )
    )


@router.post("/signup", response_model=UserPublic)
def register_user(
    user_in: UserRegister,
    db: Session = Depends(database.get_db),
):
    """
    Create new user without the need to be logged in.
    """
    user = user_crud.get_user_by_email(db, user_in.email_address)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system",
        )
    user = user_crud.get_user_by_username(db, user_in.username)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system",
        )

    user = user_crud.create_user(db, user_in)
    return user
