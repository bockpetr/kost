from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from jose import jwt, JWTError

from app.api.routers import register_routers

def create_app() -> FastAPI:
    app = FastAPI(title="Kost vin")
    
    app.mount("/static", StaticFiles(directory="app/static"), name="static")
    app.state.templates = Jinja2Templates(directory="app/templates")
    
    register_routers(app)
    return app

app = create_app()