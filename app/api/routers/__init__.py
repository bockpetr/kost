from fastapi import FastAPI
from .home import router as home_router
from .users import router as users_router
from .auth import router as auth_router
from .vina import router as vina_router
from .rocniky import router as rocniky_router

def register_routers(app: FastAPI) -> None:
    app.include_router(home_router, tags=["home"])
    app.include_router(users_router, prefix="/users", tags=["users"])
    app.include_router(auth_router, prefix="/auth", tags=["auth"])
    app.include_router(vina_router, prefix="/vina", tags=["vina"])
    app.include_router(rocniky_router, prefix="/rocniky", tags=["rocniky"])