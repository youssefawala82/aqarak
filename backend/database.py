from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ملاحظة: استبدل 'YOUR_PASSWORD' بكلمة السر التي وضعتها لـ PostgreSQL عند التثبيت
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:0000@localhost:5432/real_estate_db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# وظيفة للحصول على جلسة اتصال بقاعدة البيانات
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


