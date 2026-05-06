from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from app.database.database import get_db
from app.model.user_model import User, RoleEnum
from app.services.auth_service import require_role

router = APIRouter(
    prefix="/api/admin",
    tags=["admin"],
    dependencies=[Depends(require_role([RoleEnum.ADMIN]))]
)

class UserResponse(BaseModel):
    id: int
    username: str
    email: str | None = None
    role: RoleEnum
    department: str | None = None
    is_active: bool

    class Config:
        from_attributes = True

class RoleUpdate(BaseModel):
    role: RoleEnum

class StatusUpdate(BaseModel):
    is_active: bool

@router.get("/users", response_model=List[UserResponse])
def get_all_users(db: Session = Depends(get_db)):
    """Lấy danh sách tất cả người dùng (Chỉ ADMIN)"""
    users = db.query(User).all()
    return users

@router.patch("/users/{user_id}/role", response_model=UserResponse)
def update_user_role(user_id: int, role_data: RoleUpdate, db: Session = Depends(get_db)):
    """Cập nhật vai trò (Role) của người dùng (Chỉ ADMIN)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.role = role_data.role
    db.commit()
    db.refresh(user)
    return user

@router.patch("/users/{user_id}/status", response_model=UserResponse)
def update_user_status(user_id: int, status_data: StatusUpdate, db: Session = Depends(get_db)):
    """Bật/tắt trạng thái hoạt động của người dùng (Chỉ ADMIN)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = status_data.is_active
    db.commit()
    db.refresh(user)
    return user
