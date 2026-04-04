from sqlalchemy import Column, Integer, String, MetaData, Table, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
import datetime
import sqlite3
# Cấu hình kết nối đến cơ sở dữ liệu SQLite
conn = sqlite3.connect('kuni.db')
print("Opened database successfully");
conn.execute('''
CREATE TABLE IF NOT EXISTS team_data(team text,

country text,
season integer,
total_goals integer);''')

conn.commit()
print("Table created successfully");
conn.close()
conn = sqlite3.connect('kuni.db')
conn.execute("INSERT INTO team_data VALUES('Real Madrid', 'Spain', 2019, 53);")
conn.execute("INSERT INTO team_data VALUES('Barcelona', 'Spain', 2019, 47);")
conn.execute("INSERT INTO team_data VALUES('Arsenal', 'UK', 2019, 52);")
conn.execute("INSERT INTO team_data VALUES('Real Madrid', 'Spain', 2018, 49);")
conn.execute("INSERT INTO team_data VALUES('Barcelona', 'Spain', 2018, 45);")
conn.execute("INSERT INTO team_data VALUES('Arsenal', 'UK', 2018, 50 );")
conn.commit()
conn = sqlite3.connect('kuni.db')
cursor = conn.execute('SELECT * FROM team_data;')
for row in cursor:
    print(row)
conn.close()
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