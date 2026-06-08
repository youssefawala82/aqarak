from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ملاحظة: استبدل 'YOUR_PASSWORD' بكلمة السر التي وضعتها لـ PostgreSQL عند التثبيت
SQLALCHEMY_DATABASE_URL = "postgresql://aqarak_db_4h4r_user:IaMTvkZ0PFei4lu4XPIb6jfn0fLj14oq@dpg-d8jg8o3eo5us73adtbi0-a.oregon-postgres.render.com/aqarak_db_4h4r"

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


