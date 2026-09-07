from urllib.parse import quote_plus

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import (
DB_USER,
DB_PASSWORD,
DB_HOST,
DB_PORT,
DB_NAME

)

encoded_password = quote_plus(DB_PASSWORD)
DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(DATABASE_URL,
echo=True, #it will print sql to logs 
pool_pre_ping=True) #keeps mysql connection alive 
SessionLocal = sessionmaker(autoflush=False, autocommit=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()