# auth.py
from fastapi import APIRouter, HTTPException, Depends, status
from models import UserCreate, UserOut, Token
from db import users_col
from pydantic import BaseModel
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt
from config import settings
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

router = APIRouter(prefix="/auth", tags=["auth"])

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed):
    return pwd_context.verify(plain_password, hashed)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def get_user_by_email(email: str):
    return users_col.find_one({"email": email})

@router.post("/signup", response_model=UserOut)
def signup(u: UserCreate):
    if get_user_by_email(u.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed = hash_password(u.password)
    doc = {
        "username": u.username,
        "name": u.name,
        "age": u.age,
        "email": u.email,
        "password": hashed,
        "created_at": datetime.utcnow()
    }
    res = users_col.insert_one(doc)
    return UserOut(id=str(res.inserted_id), username=u.username, name=u.name, age=u.age, email=u.email)

@router.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    token = create_access_token({"sub": str(user["_id"]), "email": user["email"]})
    return Token(access_token=token)

from fastapi import Header

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid auth token")
        user = users_col.find_one({"_id": users_col._MongoClient__client.get_default_database().client.get_default_database().codec_options.document_class is None})  # placeholder
    except Exception:
        from bson import ObjectId
        try:
            user = users_col.find_one({"_id": ObjectId(payload.get("sub"))})
        except Exception:
            user = None
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return {"id": str(user["_id"]), "email": user["email"], "username": user["username"]}
