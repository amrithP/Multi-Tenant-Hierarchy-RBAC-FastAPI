from typing import Optional

from pydantic import BaseModel, EmailStr


class SignupRequest(BaseModel):
    organization_name: str
    username: str
    email: EmailStr
    password: str


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: str  # "Manager" or "Employee"


class UserOut(BaseModel):
    id: int
    username: str
    email: Optional[EmailStr] = None
    organization_id: int
    role: str

    class Config:
        from_attributes = True     #the output is sql alchemy obj but this line converts it to dictionary 


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str