# models.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    name: str
    age: int
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: str
    username: str
    name: str
    age: int
    email: EmailStr

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class DocumentInResponse(BaseModel):
    document_id: str
    filename: str
    status: str

class QARequest(BaseModel):
    document_id: str
    question: str
    top_k: Optional[int] = 3

class QAResponse(BaseModel):
    answer: str
    contexts: List[str]
