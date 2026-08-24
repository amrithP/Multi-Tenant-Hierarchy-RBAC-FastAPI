from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import VALID_CLIENT_ID, VALID_CLIENT_SECRET
from app.core.security import create_access_token, hash_password, verify_password
from app.db.database import get_db
from app.models import Organization, Role, User
from app.schemas.user import SignupRequest

router = APIRouter()


@router.post("/signup")
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    existing_org = db.query(Organization).filter(
        Organization.name == payload.organization_name
    ).first()
    if existing_org:
        raise HTTPException(status_code=400, detail="Organization already exists")

    existing_user = db.query(User).filter(User.username == payload.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already taken")

    owner_role = db.query(Role).filter(Role.name == "Owner").first()
    if not owner_role:
        raise HTTPException(status_code=500, detail="Roles are not seeded yet")

    new_org = Organization(name=payload.organization_name)
    db.add(new_org)
    db.flush()

    new_user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        organization_id=new_org.id,
        role_id=owner_role.id,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "organization": new_org.name,
        "username": new_user.username,
        "role": owner_role.name,
    }


@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    if form_data.client_id != VALID_CLIENT_ID or form_data.client_secret != VALID_CLIENT_SECRET:
        raise HTTPException(status_code=401, detail="Invalid client credentials")

    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    token_data = {
        "sub": user.username,
        "user_id": user.id,
        "org_id": user.organization_id,
        "role": user.role.name,
        
    }
    token = create_access_token(token_data)
    return {"access_token": token, "token_type": "bearer"}