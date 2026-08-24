from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.db.database import Base


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String(100), unique=True, nullable=False)

    users = relationship("User", back_populates="organization")
    files = relationship("File", back_populates="organization")