from sqlalchemy import Column, Integer, String, MetaData, Table, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
import datetime
# Cấu hình kết nối đến cơ sở dữ liệu SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///./database.db"
engine= create_engine(SQLALCHEMY_DATABASE_URL,connect_args={"check_same_thread": False})
Sessionlocal= sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base= declarative_base()
#model lưu trữ danh sách file đã upload
class UploadFile_PDF(Base):
    __tablename__ ="upload_files"
    id= Column(Integer, primary_key=True, index=True)
    filename= Column(String, unique=True, index=True)
    upload_time= Column(String, default=datetime.datetime.utcnow)
# Tạo bảng trong cơ sở dữ liệu
Base.metadata.create_all(bind=engine)