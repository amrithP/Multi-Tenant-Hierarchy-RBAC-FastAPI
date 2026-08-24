from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import relationship

from app.db.database import Base


class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    filename = Column(String(255), nullable=False)
    storage_path = Column(String(500), nullable=False)
    content_type = Column(String(100))
    size = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    shared_with = Column(JSON, default=list, nullable=False)

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    organization = relationship("Organization", back_populates="files")
    uploader = relationship("User", back_populates="files")


    #An Enum is used when a variable should only be allowed to have a fixed set of possible values.
