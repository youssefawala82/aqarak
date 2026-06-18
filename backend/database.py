from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ملاحظة: استبدل 'YOUR_PASSWORD' بكلمة السر التي وضعتها لـ PostgreSQL عند التثبيت
SQLALCHEMY_DATABASE_URL = "postgresql://neondb_owner:npg_UWNvaXxcF2H7@ep-proud-pond-atwcflpl.c-9.us-east-1.aws.neon.tech/neondb?sslmode=require"

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


