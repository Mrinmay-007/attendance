import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# # MySQL connection details
# DB_USERNAME = "root"
# DB_PASSWORD = "0070100"
# DB_HOST = "localhost"  # Change if hosted elsewhere
# DB_NAME = "attendance_mng"
DB_USERNAME = "admin"
DB_PASSWORD = "0070100mdas"
DB_HOST = "aws-mysql.c3kg8w64wml4.eu-north-1.rds.amazonaws.com"  # aws
DB_NAME = "attendance_mng"


# Create database engine
DATABASE_URL = f"mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
engine = create_engine(DATABASE_URL, echo=True)

# Create session
SessionLocal = sessionmaker(bind=engine)

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your_secret_key')
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:0070100@localhost/attendance_mng"
    SQLALCHEMY_TRACK_MODIFICATIONS = False