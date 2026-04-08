from fastapi import APIRouter, Depends, HTTPException,status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas import schemas
from app.database.database import get_db
from app.model import model 
from app.auth import auth
router = APIRouter(prefix="/auth",tags=["Auth"])
@router.post("register",response_model=schemas.UserResponse)
def register(user:schemas.UserCreate,db:Session=Depends(get_db)):
    db_user = db.query(model.User).filter(model.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = auth.get_password_hash(user.password)
    new_user = model.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        role=model.RoleEnum.USER
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("login",response_model=schemas.Token)
def login(form_data:OAuth2PasswordRequestForm=Depends(),db:Session=Depends(get_db)):
    user = db.query(model.User).filter(model.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password,user.hashed_password):
        raise HTTPException(status_code=401,detail="Incorrect username or password")
    access_token = auth.create_access_token(data={"sub":user.username})
    return {"access_token":access_token,"token_type":"bearer"}

@router.get("me",response_model=schemas.UserResponse)
def read_users_me(current_user:model.User=Depends(auth.get_current_user)):
    return current_user

@router.post("logout")
def logout(current_user:model.User=Depends(auth.get_current_user)):
    return {"message":"Logout successful"}

@router.post("refreshAccessToken", response_model=schemas.Token)
def refresh_access_token(current_user:model.User=Depends(auth.get_current_user)):
    access_token = auth.create_access_token(data={"sub":current_user.username})
    return {"access_token":access_token,"token_type":"bearer"}
