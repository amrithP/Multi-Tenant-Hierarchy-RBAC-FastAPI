import os
import uuid

from fastapi import APIRouter, Depends, File as FastAPIFile, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import MAX_UPLOAD_SIZE_MB
from app.core.permissions import MANAGER, OWNER, require_roles
from app.core.security import get_current_user
from app.db.database import get_db
from app.models import File, User
from app.schemas.file import FileOut,UploadFileCount
from app.schemas.file_share import UpdateSharesRequest,SharedWithEntry
from app.schemas.pagination import Page
from app.core.exceptions import InsufficientPermissionError,FileTooLarge
from app.schemas.file import FileUploadResult,MultiUploadResponse  #only did schema changes for multiple files upload at once
from typing import List
from sqlalchemy import func

router = APIRouter(prefix="/files", tags=["files"])

UPLOAD_ROOT = "uploads"
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024
ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}

# view access given by default to whomever the file is shared with but we can decide whether or not to give edit access
def has_view_access(current_user: dict, file: File) -> bool:
    if current_user["role"] == OWNER:
        return True
    if file.uploaded_by == current_user["user_id"]:
        return True
    return any(entry["user_id"] == current_user["user_id"] for entry in (file.shared_with or []))
#Simply existing in the shared_with list already grants view access — no flag needed for it

def has_edit_access(current_user: dict, file: File) -> bool:
    if current_user["role"] == OWNER:
        return True
    if file.uploaded_by == current_user["user_id"]:
        return True
    return any(
        entry["user_id"] == current_user["user_id"] and entry.get("can_edit")   #i mentioned this explicitly because usually can_edit is set to false by default with the idea that we should not simply give away the editing control
        for entry in (file.shared_with or [])
    )


@router.post("/upload", response_model=FileOut)
def upload_file(
    upload: UploadFile = FastAPIFile(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles([OWNER, MANAGER])),
):
    #Extracts the extension and rejects anything not .csv/.xlsx/.xls, before touching disk.
    ext = os.path.splitext(upload.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only .csv, .xlsx, .xls files are allowed")

#Creates a per-org folder (uploads/1/) and prefixes a random ID onto the filename so two uploads named the same thing never collide.
    org_folder = os.path.join(UPLOAD_ROOT, str(current_user["org_id"]))
    os.makedirs(org_folder, exist_ok=True)

    stored_name = f"{uuid.uuid4()}_{upload.filename}"
    storage_path = os.path.join(org_folder, stored_name)

#from ram/ disk(temporory) , it is being sent to the uploads folder (permanent save ) 1mb at a time(chunks).when u click swagger , the file gets sent to ram/disk 
    size_bytes = 0
    with open(storage_path, "wb") as buffer: #with open is also synchronous 
        while chunk := upload.file.read(1024 * 1024): #reads 1mb at atime and stores in chunck and hits await which turns the attention to other requests simultaneously
            size_bytes += len(chunk)
            if size_bytes > MAX_UPLOAD_SIZE_BYTES:
                buffer.close()
                os.remove(storage_path)
                raise FileTooLarge(f"File exceeds {MAX_UPLOAD_SIZE_MB}MB limit")
            buffer.write(chunk) # this is synchronous

    new_file = File(
        filename=upload.filename,
        storage_path=storage_path,
        content_type=upload.content_type,
        size=size_bytes,
        organization_id=current_user["org_id"],
        uploaded_by=current_user["user_id"],
        shared_with=[],
    )
    db.add(new_file)
    db.commit()
    db.refresh(new_file)
    return new_file

#upload mutiple files at once. What if 50 users uploaded multiple files at the same time , thread pool concept is applied
@router.post("/upload-multiple", response_model=MultiUploadResponse)
def upload_multiple_files(
    uploads: List[UploadFile] = FastAPIFile(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles([OWNER, MANAGER])),
):
    if len(uploads) > 10:
        raise HTTPException(status_code=400, detail="Too many files. Maximum 10 files allowed.")

    results = []
          #here , dont raise exception for a single file that is out of allowed extensions.Because there are also other files being uploaded
    for upload in uploads:
        ext = os.path.splitext(upload.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            results.append(FileUploadResult(filename=upload.filename, success=False, error="Only .csv, .xlsx, .xls files are allowed"))
            continue

        org_folder = os.path.join(UPLOAD_ROOT, str(current_user["org_id"]))
        os.makedirs(org_folder, exist_ok=True)

        stored_name = f"{uuid.uuid4()}_{upload.filename}"
        storage_path = os.path.join(org_folder, stored_name)

        size_bytes = 0
        try:
            with open(storage_path, "wb") as buffer:
                while chunk := upload.file.read(1024 * 1024):
                    size_bytes += len(chunk)
                    if size_bytes > MAX_UPLOAD_SIZE_BYTES:
                        raise FileTooLarge(f"File exceeds {MAX_UPLOAD_SIZE_MB}MB limit")
                    buffer.write(chunk)
        except FileTooLarge as e:
            os.remove(storage_path)   #delete the half stored from the uploads folder itself
            results.append(FileUploadResult(filename=upload.filename, success=False, error=e.message))
            continue

        new_file = File(
            filename=upload.filename,
            storage_path=storage_path,
            content_type=upload.content_type,
            size=size_bytes,
            organization_id=current_user["org_id"],
            uploaded_by=current_user["user_id"],
            shared_with=[],
        )
        db.add(new_file)
        db.commit()
        db.refresh(new_file)
        results.append(FileUploadResult(filename=upload.filename, success=True, file_id=new_file.id))

    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]

    return MultiUploadResponse(
        total_files=len(uploads),
        successful=len(successful),
        failed=len(failed),
        results=results,
    )




























@router.get("", response_model=Page[FileOut])
def list_files(   #query parameters eg: ?skip=20&limit=10:   visible[20 : 30] so it returns 20-29items
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    limit = min(limit, 100)
    files = db.query(File).filter(File.organization_id == current_user["org_id"]).all()
    visible = [f for f in files if has_view_access(current_user, f)]  #only if there is view access , user can get
    return {"total": len(visible), "skip": skip, "limit": limit, "items": visible[skip : skip + limit]}


@router.get("/{file_id}", response_model=FileOut)
def get_file_by_id(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    file = db.query(File).filter(
        File.id == file_id, File.organization_id == current_user["org_id"]
    ).first()
    if not file or not has_view_access(current_user, file):
        raise HTTPException(status_code=404, detail="File not found")
    return file


    







@router.get("/{file_id}/download")
def download_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    file = db.query(File).filter(
        File.id == file_id, File.organization_id == current_user["org_id"]
    ).first()
    if not file or not has_view_access(current_user, file):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file.storage_path, filename=file.filename)


@router.delete("/{file_id}")
def delete_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    file = db.query(File).filter(
        File.id == file_id, File.organization_id == current_user["org_id"]
    ).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    if not has_edit_access(current_user, file):
        raise InsufficientPermissionError("not enough permission over this file.") #custom error

    if os.path.exists(file.storage_path):
        os.remove(file.storage_path)
    db.delete(file)
    db.commit()
    return {"message": f"File '{file.filename}' deleted"}


@router.patch("/{file_id}/shares", response_model=FileOut)
def update_shares(
    file_id: int,
    payload: UpdateSharesRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    file = db.query(File).filter(
        File.id == file_id, File.organization_id == current_user["org_id"]
    ).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    if current_user["role"] != OWNER and file.uploaded_by != current_user["user_id"]:
        raise InsufficientPermissionError("not enough permission over this file.") #owner and the user who uploaded it can share

    user_ids = [e.user_id for e in payload.shared_with] #takes out just numbers from user ids [4,7]
    valid_count = db.query(User).filter(
        User.id.in_(user_ids), User.organization_id == current_user["org_id"]
    ).count()    #eg :2
    if valid_count != len(set(user_ids)):  #set removes duplicate. Keeps only one copy
        raise HTTPException(status_code=400, detail="One or more users not found in this organization")

    file.shared_with = [e.dict() for e in payload.shared_with]  #whatever we write in swagger gets updated in the table
    db.commit()
    db.refresh(file)
    return file

@router.delete("/{file_id}/share/{user_id}")
def revoke_share(
    file_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    file = db.query(File).filter(
        File.id == file_id, File.organization_id == current_user["org_id"]
    ).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    shared = file.shared_with or []  # original list of shared with ones
    updated = [e for e in shared if e["user_id"] != user_id]  #leave out the id that is to be revoked
    if len(updated) == len(shared):  #if same len ,it means it is not removed
        raise HTTPException(status_code=404, detail="Share not found")
    if not OWNER or not has_edit_access(current_user,file):
         raise InsufficientPermissionError("not enough permission over this file.")


    file.shared_with = updated
    db.commit()
    return {"message": "Access revoked"}





@router.get("/file-count>0",response_model=UploadFileCount)
def get_file_count(
        db:Session = Depends(get_db),
        current_user: dict = Depends(get_current_user)
        
):
    results=(db.query(File.uploaded_by,User.username,func.count(File.id).label("file_count")).
             join(User, File.uploaded_by == User.id).
             filter(File.organization_id == current_user["org_id"] ).
             group_by(File.uploaded_by,User.username).
             having(func.count(File.id>0))
             
            )
    return[
        {"uploaded_by":r.uploaded_by,"username":r.username,"file_count":r.file_count}
        for r in results
    ]
                                   
    
    






















#revoke 
"""Walk through it with real numbers

Say file.shared_with = [{"user_id": 2, "can_edit": false}, {"user_id": 3, "can_edit": true}] — bob (2) and carol (3) both have access. The Owner wants to revoke carol's (user_id=3).

shared = file.shared_with or []

shared = the current list — [{"user_id": 2, ...}, {"user_id": 3, ...}], 2 entries.

updated = [e for e in shared if e["user_id"] != user_id]

Builds a new list keeping only entries that aren't the person being revoked. Since user_id=3 matches carol's entry, it gets left out. updated = [{"user_id": 2, ...}] — 1 entry.

if len(updated) == len(shared):
    raise HTTPException(status_code=404, detail="Share not found")

Compares the count before (shared, 2 entries) and after (updated, 1 entry). They're different (2 ≠ 1), so this if is False — meaning something genuinely got removed, so it skips the error and continues on to save updated as the new list.


"""

"""So, short answer to "where is it before RAM"

Before it ever reaches your server at all, it's just a file on the uploading user's own computer. Between "left their computer" and "arrived in your function," it exists as network packets in transit — there's no persistent storage step in between; it's the server (via Starlette's UploadFile) that first buffers it, either in RAM or an auto-created temp file on the server's disk, before your upload_file function gets a chance to read and permanently save it."""
