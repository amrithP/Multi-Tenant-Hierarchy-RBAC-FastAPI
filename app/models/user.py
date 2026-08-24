from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100))
    hashed_password = Column(String(255))

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)

    organization = relationship("Organization", back_populates="users")
    role = relationship("Role", back_populates="users")
    files = relationship("File", back_populates="uploader")