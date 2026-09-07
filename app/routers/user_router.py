from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.permissions import MANAGER, OWNER, require_roles
from app.core.security import get_current_user, hash_password, verify_password
from app.db.database import get_db
from app.models import Role, User
from app.schemas.pagination import Page
from app.schemas.user import PasswordChange, UserCreate, UserOut, UserUpdate
from typing import Optional
from sqlalchemy import or_
from app.core.email import send_password_changed_email
from app.core.exceptions import InsufficientPermissionError

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserOut)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles([OWNER])),
):
    role = db.query(Role).filter(Role.name == payload.role).first()
    if not role or role.name == "Owner":
        raise HTTPException(status_code=400, detail="Role must be Manager or Employee")

    existing = db.query(User).filter(User.username == payload.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")

    new_user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        organization_id=current_user["org_id"],
        role_id=role.id,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "id": new_user.id,
        "username": new_user.username,
        "email": new_user.email,
        "organization_id": new_user.organization_id,
        "role": role.name,
    }


"""@router.get("", response_model=Page[UserOut])
def list_users(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles([OWNER, MANAGER])),
):
    limit = min(limit, 100)
    query = db.query(User).filter(User.organization_id == current_user["org_id"])
    total = query.count()
    users = query.offset(skip).limit(limit).all()

    items = [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "organization_id": u.organization_id,
            "role": u.role.name,
        }
        for u in users
    ]
    return {"total": total, "skip": skip, "limit": limit, "items": items}"""


@router.get("", response_model=Page[UserOut])
def list_users(  #all are query
    search: Optional[str] = None,
    role: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles([OWNER, MANAGER])),
):
    limit = min(limit, 100)
    query = db.query(User).filter(User.organization_id == current_user["org_id"])

    if search:
        like = f"%{search}%"
        query = query.filter(or_(User.username.ilike(like), User.email.ilike(like)))

    if role:
        query = query.join(Role).filter(Role.name == role)

    total = query.count()
    users = query.offset(skip).limit(limit).all()

    items = [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "organization_id": u.organization_id,
            "role": u.role.name,
        }
        for u in users
    ]
    return {"total": total, "skip": skip, "limit": limit, "items": items}


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles([OWNER])),
):
    user = db.query(User).filter(
        User.id == user_id, User.organization_id == current_user["org_id"]
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = payload.model_dump(exclude_unset=True)

    if "username" in update_data:
        clash = db.query(User).filter(
            User.username == update_data["username"], User.id != user_id
        ).first()
        if clash:
            raise HTTPException(status_code=400, detail="Username already taken")
        user.username = update_data["username"]

    if "email" in update_data:
        user.email = update_data["email"]

    if "role" in update_data:
        role = db.query(Role).filter(Role.name == update_data["role"]).first()
        if not role:
            raise HTTPException(status_code=400, detail="Invalid role")
        user.role_id = role.id

    db.commit()
    db.refresh(user)

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "organization_id": user.organization_id,
        "role": user.role.name,
    }


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles([OWNER])),
):
    user = db.query(User).filter(
        User.id == user_id, User.organization_id == current_user["org_id"]
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()
    return {"message": f"User '{user.username}' deleted"}


@router.post("/{user_id}/change-password")
def change_password(
    user_id: int,
    payload: PasswordChange,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user = db.query(User).filter(
        User.id == user_id, User.organization_id == current_user["org_id"]
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if current_user["username"] != user.username and current_user["role"] != OWNER:
        raise InsufficientPermissionError("not enough permission for changing the password.")

    if not verify_password(payload.current_password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Current password is incorrect")

    user.hashed_password = hash_password(payload.new_password)
    user.refresh_token = None    #session unvalidating step
    user.refresh_token_expires = None
    db.commit()

    try:
        send_password_changed_email(user.email, user.username)
    except Exception:
        pass

    return {"message": "Password updated successfully"}

@router.get("", response_model=Page[UserOut])
def list_users(  #all are query
    search: Optional[str] = None,
    role: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles([OWNER, MANAGER])),
):
    limit = min(limit, 100)
    query = db.query(User).filter(User.organization_id == current_user["org_id"])

    if search:  #optional. enter a part of username or email 
        like = f"%{search}%" # % is for sql
        query = query.filter(or_(User.username.ilike(like), User.email.ilike(like))) # either a part of username or password

    if role:
        query = query.join(Role).filter(Role.name == role)

    total = query.count()
    users = query.offset(skip).limit(limit).all()

    items = [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "organization_id": u.organization_id,
            "role": u.role.name,
        }
        for u in users
    ]
    return {"total": total, "skip": skip, "limit": limit, "items": items}

