from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import os

from app.database.database import get_db
from app.model.user_model import User, RoleEnum
from app.schemas import schemas

SECRET_KEY = "my_super_secret_key_for_this_project" # Replace with real secret in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440 # 1 day

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except JWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user

def get_current_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role != RoleEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user

def delete_user(user_id: int, current_user: User, db: Session):
    """
    Xóa user.
    - Admin có quyền xóa bất kỳ ai.
    - User có quyền tự xóa chính mình.
    """
    if current_user.id != user_id and current_user.role != RoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="Bạn không có quyền xóa user này")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User không tồn tại")

    db.delete(user)
    db.commit()
    return {"message": "Xóa user thành công"}


def update_user(user_id: int, update_data: schemas.UserUpdate, current_user: User, db: Session):
    """
    Cập nhật thông tin user.
    - Admin có quyền cập nhật cho bất kỳ ai.
    - User có quyền tự cập nhật thông tin chính mình.
    - Chỉ Admin mới có quyền cập nhật trường 'role'.
    """
    # 1. Kiểm tra quyền sở hữu hoặc admin
    if current_user.id != user_id and current_user.role != RoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="Bạn không có quyền cập nhật user này")

    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User không tồn tại")

    # 2. Xử lý dữ liệu cập nhật
    update_dict = update_data.model_dump(exclude_unset=True)

    # 3. Kiểm tra quyền đổi role
    if "role" in update_dict:
        if current_user.role != RoleEnum.ADMIN:
            raise HTTPException(status_code=403, detail="Chỉ Admin mới có quyền thay đổi vai trò")

    # 4. Xử lý băm mật khẩu nếu có
    if "password" in update_dict:
        update_dict["hashed_password"] = get_password_hash(update_dict.pop("password"))

    # 5. Kiểm tra trùng lặp username
    if "username" in update_dict and update_dict["username"] != db_user.username:
        existing_user = db.query(User).filter(User.username == update_dict["username"]).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username đã tồn tại")

    # 6. Cập nhật vào DB
    for key, value in update_dict.items():
        setattr(db_user, key, value)

    db.commit()
    db.refresh(db_user)
    return db_user