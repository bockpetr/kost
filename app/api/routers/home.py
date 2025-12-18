from fastapi import APIRouter, Request, Depends, HTTPException
from typing import Optional
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies import get_template_context
from app.repositories.rocniky import get_nejnovejsi_rocnik, get_rocnik_by_id
from app.repositories.vina import get_vina_by_rocnik, get_vino_detail
from app.repositories.users import get_public_user_detail

router = APIRouter()

@router.get("/")
def home_page(
    ctx: dict = Depends(get_template_context),
    rocnik_id: Optional[int] = None, 
    db: Session = Depends(get_db)
):
    """
    Zobrazí úvodní stránku se seznamem vín.
    
    Pokud není specifikován 'rocnik_id', zobrazí se vína z nejnovějšího ročníku.
    """
    selected_rocnik = None

    if rocnik_id:
        selected_rocnik = get_rocnik_by_id(db, rocnik_id)
    
    if not selected_rocnik:
        selected_rocnik = get_nejnovejsi_rocnik(db)
    
    vina = []
    rocnik_nazev = "V databázi nejsou žádné ročníky"

    if selected_rocnik:
        rocnik_nazev = f"Ročník {selected_rocnik.rok}"
        if not selected_rocnik.is_active:
            rocnik_nazev += " (Archiv)"
        vina = get_vina_by_rocnik(db, selected_rocnik.id)

    return ctx["request"].app.state.templates.TemplateResponse(
        "index.html",
        {
            **ctx,
            "active_rocnik": selected_rocnik, 
            "rocnik_nazev": rocnik_nazev,
            "vina": vina
        }
    )

@router.get("/vino/{vino_id}")
def vino_detail(
    vino_id: int,
    ctx: dict = Depends(get_template_context),
    db: Session = Depends(get_db)
):
    """
    Zobrazí detail konkrétního vína včetně hodnocení.
    """
    vino, hodnoceni = get_vino_detail(db, vino_id)
    if not vino:
        raise HTTPException(status_code=404, detail="Víno nenalezeno")
        
    return ctx["request"].app.state.templates.TemplateResponse(
        "detail_vino.html", 
        {**ctx, "vino": vino, "hodnoceni": hodnoceni}
    )
    
@router.get("/vinar/{vinar_id}")
def vinar_detail(
    vinar_id: int,
    ctx: dict = Depends(get_template_context),
    db: Session = Depends(get_db)
):
    """
    Zobrazí veřejný profil vinaře a jeho vína.
    """
    vinar = get_public_user_detail(db, vinar_id)
    
    if not vinar:
        raise HTTPException(status_code=404, detail="Vinař nenalezen")
        
    return ctx["request"].app.state.templates.TemplateResponse(
        "detail_vinar.html", 
        {**ctx, "vinar": vinar}
    )