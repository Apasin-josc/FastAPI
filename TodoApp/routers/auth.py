from fastapi import APIRouter, Depends
from pydantic import BaseModel
from models import Users
from passlib.context import CryptContext
from typing import Annotated
from database import SessionLocal
from sqlalchemy.orm import Session
from starlette import status

"""
APIRouter will allow us to be able to route from our main.py file to our auth.py file
bcrypt for hashing the password pip install passlib  // pip install bcrypt==4.0.1
"""

router = APIRouter()


bcrypt_context = CryptContext(schemes= ['bcrypt'], deprecated= 'auto')

class CreateUserRequest(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
    password: str
    role: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

@router.post("/auth", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency,
                      create_user_request: CreateUserRequest):
    create_user_model = Users(
        email= create_user_request.email,
        username= create_user_request.username,
        first_name= create_user_request.first_name,
        last_name = create_user_request.last_name,
        role= create_user_request.role,
        hashed_password= bcrypt_context.hash(create_user_request.password),
        is_active= True
    )

    #return create_user_model
    db.add(create_user_model)
    db.commit()