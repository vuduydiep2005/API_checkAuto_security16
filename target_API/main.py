from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import FastAPI, Depends, HTTPException, status,UploadFile, File
from sqlalchemy.orm import Session
import database
from database import User, get_db
from pydantic import BaseModel
import time
from jose import jwt, JWTError 
import os
from dotenv import load_dotenv
from typing import Optional, Union
from fastapi.security import OAuth2PasswordBearer
from database import SessionLocal


app = FastAPI()
@app.on_event("startup")
def create_default_admin():
    db = SessionLocal()
    admin = db.query(User).filter(User.username == "admin").first()

    if not admin:
        new_admin = User(
            username="admin",
            password="password",
            Ten="Administrator",
            Tuoi="18",
            role="admin",
            is_active=True
        )
        db.add(new_admin)
        db.commit()
        print("✔ Admin mac dinh da duoc tao")

    db.close()

@app.get("/")
def read_root():
    return {"message": "API đang chạy!"}

load_dotenv()
SECRET_KEY = "my-super-secret-key"
ALGORITHM = "HS256"

class LoginRequest(BaseModel):
    username: str
    password: str

class UserCreate(BaseModel):
    Id: int
    username: str
    password: str
    Ten: Optional[str] = None
    Tuoi: Optional[Union[int, str]] = None

class UserUpdate(BaseModel):
    Ten: Optional[str] = None
    Tuoi: Optional[int] = None

class CreateAccountRequest(BaseModel):
    username: str
    password: str
    
class UpdateRoleRequest(BaseModel):
    role: str

# API tạo token
@app.post("/token")
def generate_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == form_data.username).first()

    if not user or user.password != form_data.password:
        raise HTTPException(status_code=401, detail="Sai tai khoan hoac mat khau")

    #if not user.is_active:
        #raise HTTPException(status_code=403, detail="Tai khoan da bi khoa")

    token_payload = {
        "sub": user.username,
        "role": user.role,
        "exp": time.time() + 3600
    }

    access_token = jwt.encode(token_payload, SECRET_KEY, algorithm=ALGORITHM)

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        role = payload.get("role")

        if username is None:
            raise HTTPException(status_code=401, detail="Token khong hop le")

        return {"username": username, "role": role}

    except JWTError:
        raise HTTPException(status_code=401, detail="Token het han hoac khong hop le")

# API lấy danh sách user
@app.get("/users")
def get_users(
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Khong co quyen")

    return db.query(User).all()

@app.get("/users/{user_id}")  
def get_user(user_id: int, db: Session = Depends(get_db), username: str = Depends(verify_token)):
    user = db.query(User).filter(User.Id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User khong ton tai")
    return user

# API thêm user
@app.post("/users")
def create_user(user: UserCreate, db: Session = Depends(get_db), username: str = Depends(verify_token)):
    new_user = User(Id=user.Id, Ten=user.Ten, Tuoi=user.Tuoi, username = user.username, password = user.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# API cập nhật user
@app.put("/users/{user_id}")
def update_user(user_id: int, user: UserUpdate, db: Session = Depends(get_db),username: str = Depends(verify_token)):
    db_user = db.query(User).filter(User.Id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Khong tim thay User!!!")
    if not any([user.Ten, user.Tuoi]):
        raise HTTPException(status_code=400, detail="Khong co du lieu de cap nhat")
    if user.Ten is not None:
        db_user.Ten = user.Ten
    if user.Tuoi is not None:
        db_user.Tuoi = user.Tuoi
    db.commit()
    db.refresh(db_user)
    return db_user

# API xóa user
@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db),username: str = Depends(verify_token)):
    db_user = db.query(User).filter(User.Id == user_id).first()
    #if not db_user:
        #raise HTTPException(status_code=404, detail="Khong tim thay User")
    if db_user:
        db.delete(db_user)
        db.commit()
    return {"message": "xoa User thanh cong"}

@app.put("/users/{user_id}/lock")
def lock_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Chi admin moi co quyen")

    user = db.query(User).filter(User.Id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User khong ton tai")

    user.is_active = False
    db.commit()

    return {"message": "Da khoa tai khoan"}

@app.put("/users/{user_id}/unlock")
def unlock_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Chi admin moi co quyen")

    user = db.query(User).filter(User.Id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User khong ton tai")

    user.is_active = True
    db.commit()

    return {"message": "Da mo khoa tai khoan"}

@app.put("/users/{user_id}/role")
def update_role(
    user_id: int,
    data: UpdateRoleRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Chi admin moi co quyen")

    user = db.query(User).filter(User.Id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User khong ton tai")

    user.role = data.role
    db.commit()

    return {"message": f"Da cap quyen {data.role} cho user"}
