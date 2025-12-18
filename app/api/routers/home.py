# soubor: kost/app/api/routers/home.py
from fastapi import APIRouter, Request, Depends, HTTPException
from typing import Optional
from sqlalchemy.orm import Session
from app.core.database import get_db

# Importujeme naši novou dependency
from app.dependencies import get_template_context

from app.repositories.rocniky import get_nejnovejsi_rocnik, get_rocnik_by_id
from app.repositories.vina import get_vina_by_rocnik, get_vino_detail
from app.repositories.users import get_public_user_detail

router = APIRouter()

@router.get("/")
def home_page(
    # Vložíme dependency. FastAPI to vykoná před touto funkcí.
    # ctx bude obsahovat slovník: {'user': ..., 'all_rocniky': ..., ...}
    ctx: dict = Depends(get_template_context),
    
    rocnik_id: Optional[int] = None, 
    db: Session = Depends(get_db)
):
    # Z kontextu si můžeme vytáhnout data, pokud je potřebujeme i tady v logice
    # Např: active_rocnik = ctx["active_rocnik"]
    
    zobrazeny_rocnik = get_nejnovejsi_rocnik(db)
    selected_rocnik = None

    if rocnik_id:
        selected_rocnik = get_rocnik_by_id(db, rocnik_id)
    
    if not selected_rocnik:
        selected_rocnik = zobrazeny_rocnik
    
    vina = []
    rocnik_nazev = "V databázi nejsou žádné ročníky"

    if selected_rocnik:
        rocnik_nazev = f"Ročník {selected_rocnik.rok}"
        if not selected_rocnik.is_active:
            rocnik_nazev += " (Archiv)"
        vina = get_vina_by_rocnik(db, selected_rocnik.id)

    # DŮLEŽITÉ: Do šablony rozbalíme kontext (**ctx)
    # Tím se do šablony dostane 'user', 'all_rocniky', atd., které potřebuje base.html
    return ctx["request"].app.state.templates.TemplateResponse(
        "index.html",
        {
            **ctx,  # <--- Tady je to kouzlo. Přidá user, roles, all_rocniky...
            "active_rocnik": zobrazeny_rocnik, 
            "rocnik_nazev": rocnik_nazev,
            "vina": vina
        }
    )

# Stejně upravíme i další endpointy, které vrací HTML:

@router.get("/vino/{vino_id}")
def vino_detail(
    vino_id: int,
    ctx: dict = Depends(get_template_context),
    db: Session = Depends(get_db)
):
    vino, ratings = get_vino_detail(db, vino_id)
    if not vino:
        raise HTTPException(status_code=404, detail="Víno nenalezeno")
        
    return ctx["request"].app.state.templates.TemplateResponse(
        "detail_vino.html", 
        {**ctx, "vino": vino, "ratings": ratings} # Rozbalit ctx
    )
    
@router.get("/vinar/{vinar_id}")
async def vinar_detail(
    vinar_id: int,
    ctx: dict = Depends(get_template_context),
    db: Session = Depends(get_db)
):
    # Načtení detailu vinaře z DB
    vinar = get_public_user_detail(db, vinar_id)
    
    if not vinar:
        raise HTTPException(status_code=404, detail="Vinař nenalezen")
        
    # Vykreslení šablony
    return ctx["request"].app.state.templates.TemplateResponse(
        "detail_vinar.html", 
        {**ctx, "vinar": vinar}  # Posíláme data pod klíčem 'vinar'
    )