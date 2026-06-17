"""Auth API — login, register, token."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from datetime import datetime, timezone
from core.database import get_db
from core.security import verify_password, hash_password, create_token, get_current_user
from models.models import User, UserRole, Ranger, Visitor, Volunteer

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    username: str
    email: str
    full_name: str
    password: str
    role: str = "visitor"


@router.post("/token")
async def login(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == form.username))
    user = result.scalars().first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")
    user.last_login = datetime.now(timezone.utc)
    await db.commit()
    token = create_token({"sub": user.username, "role": user.role.value, "id": user.id})
    return {
        "access_token": token, "token_type": "bearer",
        "role": user.role.value, "username": user.username, "full_name": user.full_name
    }


@router.post("/register", status_code=201)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.username == req.username))
    if existing.scalars().first():
        raise HTTPException(status_code=409, detail="Username already exists")
    email_check = await db.execute(select(User).where(User.email == req.email))
    if email_check.scalars().first():
        raise HTTPException(status_code=409, detail="Email already registered")
    role_map = {
        "admin": UserRole.ADMIN, "ranger": UserRole.RANGER,
        "visitor": UserRole.VISITOR, "volunteer": UserRole.VOLUNTEER
    }
    role = role_map.get(req.role, UserRole.VISITOR)
    user = User(
        username=req.username, email=req.email, full_name=req.full_name,
        hashed_password=hash_password(req.password), role=role
    )
    db.add(user)
    await db.flush()
    # Create role profile
    if role == UserRole.RANGER:
        import random
        db.add(Ranger(
            user_id=user.id,
            badge_number=f"R{str(user.id).zfill(3)}",
            sector="Zone-A",
            current_lat=11.4916 + random.uniform(-0.05, 0.05),
            current_lon=76.9294 + random.uniform(-0.05, 0.05)
        ))
    elif role == UserRole.VISITOR:
        db.add(Visitor(user_id=user.id))
    elif role == UserRole.VOLUNTEER:
        db.add(Volunteer(user_id=user.id))
    await db.commit()
    return {"message": "User registered successfully", "username": req.username, "role": req.role}


@router.get("/me")
async def get_me(db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)):
    result = await db.execute(select(User).where(User.username == user["username"]))
    u = result.scalars().first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": u.id, "username": u.username, "email": u.email,
        "full_name": u.full_name, "role": u.role.value, "is_active": u.is_active
    }
