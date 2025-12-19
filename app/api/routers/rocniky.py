from datetime import datetime
from fastapi import APIRouter, Request, Depends, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies import get_template_context, require_admin
from app.models.db import Rocnik, Vino, Hodnoceni
from app.repositories.rocniky import (
    get_vsechny_rocniky, 
    set_active_rocnik_logic, 
    deactivate_rocnik_logic,
    get_rocnik_by_id,
    get_nejnovejsi_rocnik
)

router = APIRouter()

@router.get("/sprava")
def sprava_rocniku(
    request: Request,
    ctx: dict = Depends(get_template_context),
    db: Session = Depends(get_db),
    admin_check: dict = Depends(require_admin)
):
    """Zobrazí stránku pro správu ročníků."""
    rocniky = get_vsechny_rocniky(db)

    return ctx["request"].app.state.templates.TemplateResponse(
        "sprava_rocniku.html",
        {
            **ctx, 
            "rocniky": rocniky
        }
    )

@router.post("/pridat")
def pridat_rocnik(
    ctx: dict = Depends(get_template_context),
    db: Session = Depends(get_db),
    admin_check: dict = Depends(require_admin)
):
    """Vytvoří nový ročník (automaticky rok + 1)."""
    nejnovejsi = get_nejnovejsi_rocnik(db)
    if nejnovejsi:
        novy_rok_cislo = nejnovejsi.rok + 1
    else:
        novy_rok_cislo = datetime.now().year

    novy_rocnik = Rocnik(rok=novy_rok_cislo, is_active=False)
    
    db.add(novy_rocnik)
    db.commit()

    return RedirectResponse("/rocniky/sprava", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/aktivovat/{rocnik_id}")
def aktivovat_rocnik(
    rocnik_id: int,
    ctx: dict = Depends(get_template_context),
    db: Session = Depends(get_db),
    admin_check: dict = Depends(require_admin)
):
    """
    Aktivuje ročník.
    Je možné aktivovat pouze NEJNOVĚJŠÍ ročník.
    """
    nejnovejsi = get_nejnovejsi_rocnik(db)
    
    if nejnovejsi and (nejnovejsi.id == rocnik_id):
        set_active_rocnik_logic(db, rocnik_id)
    
    return RedirectResponse("/rocniky/sprava", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/deaktivovat/{rocnik_id}")
def deaktivovat_rocnik(
    rocnik_id: int,
    ctx: dict = Depends(get_template_context),
    db: Session = Depends(get_db),
    admin_check: dict = Depends(require_admin)
):
    """
    Deaktivuje ročník.
    """
    deactivate_rocnik_logic(db, rocnik_id)
    
    return RedirectResponse("/rocniky/sprava", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/smazat/{rocnik_id}")
def smazat_rocnik(
    rocnik_id: int,
    ctx: dict = Depends(get_template_context),
    db: Session = Depends(get_db),
    admin_check: dict = Depends(require_admin)
):
    """
    Smaže ročník i se všemi víny a jejich hodnocením v daném ročníku
    díky parametrům cascade="all, delete-orphan" v db.py
    """
    rocnik = get_rocnik_by_id(db, rocnik_id)
    
    if rocnik:
        db.delete(rocnik)
        db.commit()

    return RedirectResponse("/rocniky/sprava", status_code=status.HTTP_303_SEE_OTHER)