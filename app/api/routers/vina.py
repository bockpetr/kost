from fastapi import APIRouter, Request, Depends, Form, status, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session, aliased
from typing import Optional

from app.core.database import get_db
from app.dependencies import get_template_context, get_current_user
from app.repositories.users import get_user_by_login
from app.repositories.rocniky import get_aktivni_rocnik
from app.repositories.vina import get_vina_by_vinar
from app.models.db import Vino, Hodnoceni, Users

router = APIRouter()

@router.get("/sprava")
def manage_vina(
    request: Request,
    ctx: dict = Depends(get_template_context),
    db: Session = Depends(get_db),
    user: Users = Depends(get_current_user)
):
    
    active_rocnik = get_aktivni_rocnik(db)
    
    vina = []
    if user and active_rocnik:
        vina = get_vina_by_vinar(db, active_rocnik.id, user.id)

    return ctx["request"].app.state.templates.TemplateResponse(
        "sprava_vin.html",
        {
            **ctx, 
            "vina": vina,
            "active_rocnik": active_rocnik
        }
    )

@router.get("/pridat")
def pridat_vino_page(
    request: Request,
    ctx: dict = Depends(get_template_context),
    user: Users = Depends(get_current_user)
):
        
    return ctx["request"].app.state.templates.TemplateResponse(
        "pridat_vino.html",
        {**ctx}
    )

@router.post("/pridat")
def pridat_vino_submit(
    request: Request,
    nazev: str = Form(...),
    odruda: str = Form(None),
    barva: str = Form(...),
    sladkost: str = Form(None),
    privlastek: str = Form(None),
    rok_sklizne: int = Form(...),
    ctx: dict = Depends(get_template_context),
    db: Session = Depends(get_db),
    user: Users = Depends(get_current_user)
):
    
    active_rocnik = get_aktivni_rocnik(db)
    if not active_rocnik:
        return ctx["request"].app.state.templates.TemplateResponse(
            "pridat_vino.html",
            {**ctx, "error": "Není nastaven žádný aktivní ročník!"}
        )

    nove_vino = Vino(
        nazev=nazev,
        odruda=odruda,
        barva=barva,
        sladkost=sladkost,
        privlastek=privlastek,
        rok_sklizne=rok_sklizne,
        vinar_id=user.id,
        rocnik_id=active_rocnik.id
    )
    
    db.add(nove_vino)
    db.commit()

    return RedirectResponse("/vina/sprava", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/upravit/{vino_id}")
def upravit_vino_page(
    vino_id: int,
    request: Request,
    ctx: dict = Depends(get_template_context),
    db: Session = Depends(get_db),
    user: Users = Depends(get_current_user)
):
    
    vino = db.query(Vino).filter(Vino.id == vino_id, Vino.vinar_id == user.id).first()
    
    if not vino:
        raise HTTPException(status_code=404, detail="Víno neexistuje nebo na jeho úpravu nemáte právo.")

    return ctx["request"].app.state.templates.TemplateResponse(
        "upravit_vino.html",
        {**ctx, "vino": vino}
    )

@router.post("/upravit/{vino_id}")
def upravit_vino_submit(
    vino_id: int,
    request: Request,
    nazev: str = Form(...),
    odruda: str = Form(None),
    barva: str = Form(...),
    sladkost: str = Form(None),
    privlastek: str = Form(None),
    rok_sklizne: int = Form(...),
    ctx: dict = Depends(get_template_context),
    db: Session = Depends(get_db),
    user: Users = Depends(get_current_user)
):
    
    vino = db.query(Vino).filter(Vino.id == vino_id, Vino.vinar_id == user.id).first()
    
    if not vino:
        raise HTTPException(status_code=404, detail="Víno neexistuje.")

    vino.nazev = nazev
    vino.odruda = odruda
    vino.barva = barva
    vino.sladkost = sladkost
    vino.privlastek = privlastek
    vino.rok_sklizne = rok_sklizne
    
    db.commit()
    
    return RedirectResponse("/vina/sprava", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/smazat/{vino_id}")
def smazat_vino(
    vino_id: int,
    ctx: dict = Depends(get_template_context),
    db: Session = Depends(get_db),
    user: Users = Depends(get_current_user)
):
    
    vino = db.query(Vino).filter(Vino.id == vino_id, Vino.vinar_id == user.id).first()
    
    if not vino:
        raise HTTPException(status_code=404, detail="Víno nenalezeno nebo nemáte oprávnění jej smazat.")
        
    db.delete(vino)
    db.commit()
    
    return RedirectResponse("/vina/sprava", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/hodnoceni")
def hodnoceni_page(
    request: Request,
    ctx: dict = Depends(get_template_context),
    db: Session = Depends(get_db),
    user: Users = Depends(get_current_user)
):
    
    active_rocnik = get_aktivni_rocnik(db)
    
    if not active_rocnik:
         return ctx["request"].app.state.templates.TemplateResponse(
            "hodnoceni.html", {**ctx, "error": "Není aktivní ročník.", "vina_data": []}
        )

    MojeHodnoceni = aliased(Hodnoceni)

    results = (
        db.query(Vino, MojeHodnoceni)
        .join(Vino.vinar)
        .outerjoin(MojeHodnoceni, (MojeHodnoceni.vino_id == Vino.id) & (MojeHodnoceni.hodnotitel_id == user.id))
        .filter(Vino.rocnik_id == active_rocnik.id)
        .filter(Vino.vinar_id != user.id)
        .order_by(Vino.nazev)
        .all()
    )
    
    vina_data = []
    for vino, hodnoceni in results:
        vina_data.append({
            "vino": vino,
            "hodnoceni": hodnoceni
        })

    return ctx["request"].app.state.templates.TemplateResponse(
        "hodnoceni.html",
        {
            **ctx, 
            "vina_data": vina_data
        }
    )


@router.post("/hodnoceni")
async def hodnoceni_submit(
    request: Request,
    ctx: dict = Depends(get_template_context),
    db: Session = Depends(get_db),
    user: Users = Depends(get_current_user)
):
    
    form_data = await request.form()
    
    for key, value in form_data.items():
        if key.startswith("body_"):
            try:
                vino_id = int(key.split("_")[1])
                raw_body = value.strip()
                
                poznamka_key = f"poznamka_{vino_id}"
                poznamka_val = form_data.get(poznamka_key, "").strip()

                vino_db = db.query(Vino).filter(Vino.id == vino_id).first()
                if not vino_db or vino_db.vinar_id == user.id:
                    continue

                hodnoceni = db.query(Hodnoceni).filter(
                    Hodnoceni.vino_id == vino_id,
                    Hodnoceni.hodnotitel_id == user.id
                ).first()

                if raw_body:
                    body_val = int(raw_body)
                    
                    if body_val < 0: body_val = 0
                    if body_val > 100: body_val = 100

                    if hodnoceni:
                        hodnoceni.body = body_val
                        hodnoceni.poznamka = poznamka_val
                    else:
                        nove_hodnoceni = Hodnoceni(
                            body=body_val,
                            poznamka=poznamka_val,
                            vino_id=vino_id,
                            hodnotitel_id=user.id
                        )
                        db.add(nove_hodnoceni)
                else:
                    if hodnoceni:
                        db.delete(hodnoceni)
                        
            except ValueError:
                continue

    db.commit()
    
    return RedirectResponse("/vina/hodnoceni", status_code=status.HTTP_303_SEE_OTHER)