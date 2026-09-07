from fastapi import FastAPI

from app.routers import auth_router, file_router, role_router, user_router,health_router
from app.core.middleware import add_custom_header
from app.core.logger import logger
from app.core.middleware import log_middleware

app = FastAPI(title="Hierarchy Multi-Tenant RBAC API")
logger.info('Starting API...')

app.include_router(auth_router.router, tags=["auth"])
app.include_router(user_router.router)
app.include_router(role_router.router)
app.include_router(file_router.router)
app.include_router(health_router.router)

from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

from app.core.exceptions import(
    InsufficientPermissionError,
    global_server_exception,
    insufficient_permission_error,
    FileTooLarge,
    file_too_large
)












app.add_middleware(
    CORSMiddleware,         #if added frontend on this port , the reset password page might work
    allow_origins=["http://localhost:5500","http://localhost:3000"],  # frontend's exact origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.rate_limit import limiter

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

#This registers the limiter with the app and tells it what to do when someone goes over the limit — automatically return a 429 Too Many Requests response instead of processing the request. 

#app.middleware("http")(log_requests)  #custom middleware applied for all endpoints with http

# app.middleware("http")(logging)
app.middleware("http")(add_custom_header)  # u can see this in swagger , for example login endpoint
app.add_middleware(GZipMiddleware, minimum_size=1000 )   #this is built in
#this compresses the size of response if 1000 bytes or over.No need to mention endpoint. Its for global for all apis

app.add_middleware(TrustedHostMiddleware,allowed_hosts=["localhost","db","127.0.0.1"])  #restriction on hosts other than these

 # app.add_middleware(HTTPSRedirectMiddleware)        #In production, HTTP is insecure. HTTPSRedirectMiddleware automatically redirects all HTTP requests to HTTPS, ensuring secure and encrypted communication.
#running the above will not work for localhost,But in production httpsredirectmiddleware is a must 

app.middleware("http")(log_middleware)
app.add_exception_handler(InsufficientPermissionError,insufficient_permission_error) # has to be raised in an api
app.add_exception_handler(Exception,global_server_exception) #raised globally automatically when server crashes


app.add_exception_handler(FileTooLarge,file_too_large)   
