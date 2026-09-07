from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.database import get_db

router = APIRouter(tags=["health"])

# doesnt need authourization
#main purpose of health check api is to check whether server and db are alive to avoid errors during deployment
@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))   #does not touch any table in db. Check whether db is connected and alive
        db_status = "ok"
    except Exception:
        db_status = "error"

    return {"status": "ok", "database": db_status}

#include this in main.py