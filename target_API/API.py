
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Any
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# --- 1. SETUP DATABASE ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- 2. ĐỊNH NGHĨA BẢNG (KÈM LỖI CẤU TRÚC) ---
class UserDB(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    
    # [BUG 02] Xóa unique=True để cho phép trùng lặp username
    username = Column(String, index=True) 
    
    password = Column(String)
    
    # [BUG 03] Để kiểu String để nhận cả chữ "hai_muoi_mot" thay vì Integer
    age = Column(String, nullable=True) 
    
    full_name = Column(String, nullable=True)
    
    # [BUG 09] Thêm trường status để test tài khoản bị khóa
    status = Column(String, default="Active") 

Base.metadata.create_all(bind=engine)

# --- 3. MODELS INPUT (KÈM LỖI VALIDATION) ---
class UserBase(BaseModel):
    username: str
    full_name: Optional[str] = None
    # [BUG 03] Dùng Any hoặc str để Pydantic không báo lỗi khi nhập chữ vào tuổi
    age: Optional[Any] = None 
    status: str = "Active"

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    age: Optional[Any] = None

class UserResponse(UserBase):
    id: int
    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    username: str
    password: str

app = FastAPI(title="API Có Lỗi (SUT)", description="API chứa lỗi cố ý phục vụ kiểm thử")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- 4. CÁC ENDPOINT ĐÃ CẤY LỖI ---

@app.post("/users", response_model=UserResponse, status_code=201)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # [BUG 02] Lỗi Logic: Bỏ qua bước kiểm tra trùng lặp (Duplicate Check)
    # Code đúng phải là: if db.query(UserDB).filter(...).first(): raise HTTPException...
    
    new_user = UserDB(
        username=user.username,
        password=user.password,
        age=str(user.age), # Ép kiểu thành string để lưu cái sai vào DB
        full_name=user.full_name,
        status=user.status
    )
    db.add(new_user)
    
    # [BUG 05] Dữ liệu ma: Uncomment dòng dưới đây để tạo lỗi "Không commit vào DB"
    # Nếu muốn test Case 05, hãy thêm dấu # trước dòng db.commit()
    db.commit() 
    
    db.refresh(new_user)
    return new_user

@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    # Case 04: Hoạt động bình thường
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get("/users", response_model=List[UserResponse])
def get_all_users(db: Session = Depends(get_db)):
    # Case 05: Nếu ở hàm create_user bạn tắt db.commit(), hàm này sẽ không thấy user mới
    return db.query(UserDB).all()

@app.put("/users/{user_id}")
def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # [BUG 07] Logic sai: Không kiểm tra user_update có rỗng hay không
    # Vẫn trả về 200 OK dù không có gì thay đổi
    
    if user_update.full_name:
        user.full_name = user_update.full_name
    if user_update.age:
        user.age = str(user_update.age)
        
    db.commit()
    return {"message": "Update thành công", "data": user_update}

@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    
    # [BUG 11] Lỗi Logic: User không tồn tại vẫn báo xóa thành công (200 OK)
    if not user:
        # Thay vì raise HTTPException 404, ta giả vờ như đã xóa xong
        return {"message": "Đã xóa user thành công (Fake)", "id": user_id}
    
    db.delete(user)
    db.commit()
    return {"message": "Đã xóa user thành công"}

@app.post("/login")
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.username == login_data.username).first()
    
    if not user or user.password != login_data.password:
        raise HTTPException(status_code=401, detail="Login failed")
    
    # [BUG 09] Lỗi bảo mật: Không kiểm tra status "Inactive"
    # Code đúng: if user.status == "Inactive": raise HTTPException(403)...
    
    return {"token": "fake-jwt-token", "status": user.status}
