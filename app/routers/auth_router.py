from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import VALID_CLIENT_ID, VALID_CLIENT_SECRET
from app.core.security import create_access_token, hash_password, verify_password
from app.db.database import get_db
from app.models import Organization, Role, User
from app.schemas.user import SignupRequest, ForgotPasswordRequest,ResetPasswordRequest
from app.schemas.common import MessageResponse
from app.schemas.user import TokenResponse

from fastapi import Request

from app.core.rate_limit import limiter

#login validation 
from datetime import datetime, timedelta, timezone
from app.core.config import ACCOUNT_LOCKOUT_MINUTES, MAX_FAILED_LOGIN_ATTEMPTS, VALID_CLIENT_ID, VALID_CLIENT_SECRET,RESET_TOKEN_EXPIRE_MINUTES

import secrets  #forgot password and reset password 

#resend mail service provider 
from app.core.config import FRONTEND_RESET_URL
from app.core.email import send_password_changed_email, send_reset_email

router = APIRouter()


@router.post("/signup")
@limiter.limit('3/minute')   #rate limit with request
def signup(request:Request,payload: SignupRequest, db: Session = Depends(get_db)):
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


import secrets

from app.core.config import REFRESH_TOKEN_EXPIRE_DAYS
from app.schemas.user import TokenResponse


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    if form_data.client_id != VALID_CLIENT_ID or form_data.client_secret != VALID_CLIENT_SECRET:
        raise HTTPException(status_code=401, detail="Invalid client credentials")

    username = form_data.username.strip()
    password = form_data.password

    user = db.query(User).filter(User.username == username).first()

    if user and user.locked_until and user.locked_until > datetime.utcnow():
        raise HTTPException(
            status_code=423,
            detail=f"Account locked due to too many failed attempts. Try again after {user.locked_until.strftime('%H:%M:%S')} UTC",
        )

    if not user or not verify_password(password, user.hashed_password):
        if user:
            user.failed_attempts += 1
            if user.failed_attempts >= MAX_FAILED_LOGIN_ATTEMPTS:
                user.locked_until = datetime.utcnow() + timedelta(minutes=ACCOUNT_LOCKOUT_MINUTES)
                user.failed_attempts = 0
            db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    user.failed_attempts = 0
    user.locked_until = None

    access_token = create_access_token({
        "sub": user.username,
        "user_id": user.id,
        "org_id": user.organization_id,
        "role": user.role.name,
    })

    refresh_token = secrets.token_urlsafe(32)
    user.refresh_token = refresh_token
    user.refresh_token_expires = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    db.commit()

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}



@router.post("/forgot-password", response_model=MessageResponse)
@limiter.limit("3/minute")
def forgot_password(request: Request, payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()

    if user:
        token = secrets.token_urlsafe(32)  #reset token generation
        user.reset_token = token
        user.reset_token_expires = datetime.utcnow() + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)
        db.commit()

        reset_link = f"{FRONTEND_RESET_URL}?token={token}"
        try:
            send_reset_email(user.email, user.username, reset_link)
        except Exception:
            pass

    return {"message": "If that email exists, a reset link has been sent."}

@router.post("/reset-password", response_model=MessageResponse)
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.reset_token == payload.token).first()

    #If there is no user, or the reset token has no expiry time, or the expiry time has already passed, reject the reset request
    if not user or not user.reset_token_expires or user.reset_token_expires < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user.hashed_password = hash_password(payload.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    user.refresh_token = None   #session invalidation
    user.refresh_token_expires = None  #session invalidatiion
    db.commit()

    try:
        send_password_changed_email(user.email, user.username)
    except Exception as e:
        print("PASSWORD-CHANGED EMAIL FAILED:", e)

    return {"message": "Password has been reset successfully"}