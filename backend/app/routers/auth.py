import hashlib
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


def hash_password(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class LoginRequest(BaseModel):
    username: str
    password: str


class UserCreateRequest(BaseModel):
    username: str
    password: str
    full_name: str = ""
    role: str = "operation"


class ChangeCredentialsRequest(BaseModel):
    current_username: str
    current_password: str
    new_username: str = None
    new_password: str = None


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == payload.username).first()
    if not user or user.password_hash != hash_password(payload.password):
        raise HTTPException(401, "Kullanıcı adı veya şifre hatalı.")
    return {"username": user.username, "full_name": user.full_name, "role": user.role}


@router.put("/change-credentials")
def change_credentials(payload: ChangeCredentialsRequest, db: Session = Depends(get_db)):
    """
    Mevcut kullanıcı adı + şifreyi doğrulayıp, kullanıcı adı ve/veya
    şifreyi değiştirir. Güvenlik amacıyla mevcut şifrenin doğru
    girilmesi zorunludur (X-User-Role header'ına güvenilmez).
    """
    user = db.query(models.User).filter(models.User.username == payload.current_username).first()
    if not user or user.password_hash != hash_password(payload.current_password):
        raise HTTPException(401, "Mevcut kullanıcı adı veya şifre hatalı.")

    if payload.new_username:
        existing = db.query(models.User).filter(
            models.User.username == payload.new_username,
            models.User.id != user.id,
        ).first()
        if existing:
            raise HTTPException(400, "Bu kullanıcı adı zaten kullanımda.")
        user.username = payload.new_username

    if payload.new_password:
        user.password_hash = hash_password(payload.new_password)

    db.commit()
    return {"ok": True, "username": user.username}


@router.post("/users")
def create_user(payload: UserCreateRequest, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.username == payload.username).first()
    if existing:
        raise HTTPException(400, "Bu kullanıcı adı zaten mevcut.")
    user = models.User(
        username=payload.username, password_hash=hash_password(payload.password),
        full_name=payload.full_name, role=payload.role,
    )
    db.add(user)
    db.commit()
    return {"ok": True}


@router.get("/users")
def list_users(db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    return [{"id": u.id, "username": u.username, "full_name": u.full_name, "role": u.role} for u in users]
