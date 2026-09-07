from fastapi import Request
import time
from app.core.logger import logger
#custom middleware.  wire in main.py
# async def log_requests(request:Request,call_next):
#     print("Request_url:",request.url)
#     response = await call_next(request)  #call_next hands the request to the real endpoint 
#     # This is the actual handoff to your real route. await here means: "pause this middleware function, let the real route (e.g. login) run and do its work — querying the database, hashing passwords, whatever it needs — and resume me once it's done." While paused here, the event loop is free to handle other incoming requests, same concept as the await asyncio.sleep(3) example from earlier. response ends up holding whatever the real route returned.


#     return response

#logging middleware: How long a request takes to get handled at the api endpoint in milliseconds.
# async def logging(request:Request,call_next):
#     start_time=time.time()

#     response = await call_next(request)  # await is for turning the attention elsewhere to another 

#     process_time = time.time() - start_time

#     print(f"Path:{request.url.path} | Process_Time:{process_time}")
#     return response  #always return respomse


async def add_custom_header(request:Request,call_next):
    #before request reaches the route
    response = await call_next(request)   #request reaches the route
    #we will modify the response before passing it to client 
    response.headers["X-Custom-Header"] = "This is a customer header"
    return response

# http    logger middleware applied for all. So no need to manually enter logger.info
async def log_middleware(request:Request,call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time()-start_time
    log_dict = {
        'url':request.url.path,
        'method': request.method,
        'process_time': process_time
    }
    logger.info(log_dict)   #to make this extra visible in app.log , u have to include in logging.formatter
       #u can add extra = log_dict
   
    return response
     



# Basic Syntax:

# @app.middleware("http")
# async def custom_middleware(request: Request, call_next):
#     # Code before request reaches the route
#     response = await call_next(request)
#     # Code after response is generated
#     return response