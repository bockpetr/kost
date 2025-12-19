from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from app.api.routers import register_routers

def create_app() -> FastAPI:
    """
    Vytvoří a nakonfiguruje instanci FastAPI aplikace.

    Postup inicializace:
    1. Vytvoření instance FastAPI s metadaty (titulek).
    2. Připojení statických souborů (CSS, obrázky) na cestu `/static`.
    3. Inicializace Jinja2 šablon a jejich uložení do `app.state`.
    4. Registrace všech routerů (URL endpointů) z modulu `api`.

    Returns:
        FastAPI: Plně nakonfigurovaná instance aplikace připravená ke spuštění.
    """
    
    app = FastAPI(title="Kost vin")
    
    app.mount("/static", StaticFiles(directory="app/static"), name="static")
    app.state.templates = Jinja2Templates(directory="app/templates")
    
    register_routers(app)
    return app

app = create_app()