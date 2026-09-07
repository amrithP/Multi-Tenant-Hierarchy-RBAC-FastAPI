from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel
from app.schemas.file_share import SharedWithEntry


"""class SharedWithEntry(BaseModel):
    user_id: int
    can_edit: bool"""




class FileOut(BaseModel):
    id: int
    filename: str
    content_type: Optional[str] = None
    size: Optional[int] = None
    uploaded_by: int
    created_at: datetime
    shared_with: List[SharedWithEntry] = []

    class Config:
        from_attributes = True



#multiple files upload at once 
class FileUploadResult(BaseModel):
    filename: str
    success: bool
    file_id: Optional[int] = None
    error: Optional[str] = None


class MultiUploadResponse(BaseModel):
    total_files: int
    successful: int
    failed: int
    results: List[FileUploadResult]



class UploadFileCount(BaseModel):
    uploaded_by:int
    username:str
    file_count:int