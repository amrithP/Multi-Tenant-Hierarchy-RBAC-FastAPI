from fastapi import Request
from fastapi.responses import JSONResponse


#custom exception handler 
class InsufficientPermissionError(Exception):
    def __init__(self,message:str):
        self.message = message

async def insufficient_permission_error(request:Request,exc:InsufficientPermissionError):
    return JSONResponse(
        status_code=403,
        content={"detail":exc.message}
    )


#global exception
async def global_server_exception(request:Request,exc:Exception):
    print("Unhandled error:",exc)
    return JSONResponse(
        status_code=500,
        content={
            "detail":"Internal Server Error.Pls try again later. "
        }
    )

class FileTooLarge(Exception):
    def __init__(self,message:str):
        self.message=message

async def file_too_large(request:Request,exc:FileTooLarge):
    return JSONResponse(
        status_code=413,
        content={'detail':exc.message}
    )

