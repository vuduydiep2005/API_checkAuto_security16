from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()
pwd=os.getenv("pwd_db")
DB_URL = "sqlite:///./test.db"
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False,autoflush=False,bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    Id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    password = Column(String)
    Ten = Column(String, nullable=True, index=True)
    Tuoi = Column(Integer, nullable=True)
    role = Column(String, default="user")
    is_active = Column(Boolean, default=True)
def get_db():
    db=SessionLocal()
    try: 
        yield db
    finally:
        db.close()
Base.metadata.create_all(bind=engine)
