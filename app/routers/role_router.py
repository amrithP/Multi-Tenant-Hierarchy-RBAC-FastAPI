from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import Role
from app.schemas.role import RoleOut

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("", response_model=list[RoleOut])
def list_roles(db: Session = Depends(get_db)):
    return db.query(Role).all()