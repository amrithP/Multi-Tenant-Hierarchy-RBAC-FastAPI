from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.db.database import get_db

from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY



pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)   #jwt accesstoken is ready.It is shortlived like 15 mins but used to access protected routes


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login") 
#Authorization: Bearer eyJhbGciOiJIUzI1Ni...

# FastAPI extracts:

# eyJhbGciOiJIUzI1Ni...

# and gives it to:

# token


from sqlalchemy.orm import Session

from app.db.database import get_db

#this is to validate the jwt access token  and session invalidation using refresh token
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    from app.models import User  # imported here to avoid a circular import

    credential_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credential",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        username = payload.get("sub")
        user_id = payload.get("user_id")
        org_id = payload.get("org_id")
        role = payload.get("role")
        if username is None or user_id is None or org_id is None or role is None:
            raise credential_exception
    except JWTError:
        raise credential_exception

    user = db.query(User).filter(User.id == user_id).first()

    if not user or not user.refresh_token:  #this checks from the db itself as we added a column in users for refresh token
        raise credential_exception      #session unvalidating. if without logging again tried to access protected route , then throw this 

    return {"username": username, "user_id": user_id, "org_id": org_id, "role": role}