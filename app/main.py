from fastapi import FastAPI

from app.routers import auth_router, file_router, role_router, user_router

app = FastAPI(title="Hierarchy Multi-Tenant RBAC API")

app.include_router(auth_router.router, tags=["auth"])
app.include_router(user_router.router)
app.include_router(role_router.router)
app.include_router(file_router.router)