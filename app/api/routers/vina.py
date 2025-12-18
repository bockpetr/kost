from fastapi import APIRouter, Request, Depends, Form, status, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session, aliased
from typing import Optional

from app.core.database import get_db
from app.dependencies import get_template_context
from app.repositories.users import get_user_by_login
from app.repositories.rocniky import get_aktivni_rocnik
from app.repositories.vina import get_wines_by_vinar
from app.models.db import Vino, Hodnoceni, Users

router = APIRouter()

@router.get("/sprava")
def manage_wines(
    request: Request,
    ctx: dict = Depends(get_template_context),
    db: Session = Depends(get_db)
):
    # 1. Zjistit, kdo je přihlášený (podle kontextu z dependencies)
    username = ctx.get("user")
    if not username:
        return RedirectResponse("/auth/login", status_code=303)
    
    # 2. Načíst objekt uživatele z DB, abychom měli jeho ID
    user = get_user_by_login(db, username)
    
    # 3. Zjistit aktivní ročník (vína spravujeme obvykle pro aktuální ročník)
    active_rocnik = get_aktivni_rocnik(db)
    
    wines = []
    if user and active_rocnik:
        # 4. Načíst vína tohoto vinaře v daném ročníku
        wines = get_wines_by_vinar(db, active_rocnik.id, user.id)

    return ctx["request"].app.state.templates.TemplateResponse(
        "sprava_vin.html",
        {
            **ctx, 
            "wines": wines,
            "active_rocnik": active_rocnik
        }
    )

@router.get("/pridat")
def pridat_vino_page(
    request: Request,
    ctx: dict = Depends(get_template_context)
):
    # Kontrola přihlášení
    if not ctx.get("user"):
        return RedirectResponse("/auth/login", status_code=303)
        
    return ctx["request"].app.state.templates.TemplateResponse(
        "pridat_vino.html",
        {**ctx}
    )

# 2. Zpracování formuláře (Uložení do DB)
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
    db: Session = Depends(get_db)
):
    # A. Získat přihlášeného uživatele (potřebujeme jeho ID)
    username = ctx.get("user")
    if not username:
        return RedirectResponse("/auth/login", status_code=303)
    
    user = get_user_by_login(db, username)
    
    # B. Získat aktivní ročník (víno patří do ročníku)
    active_rocnik = get_aktivni_rocnik(db)
    if not active_rocnik:
        # Pokud není aktivní ročník, nelze přidat víno (ošetření chyby)
        return ctx["request"].app.state.templates.TemplateResponse(
            "pridat_vino.html",
            {**ctx, "error": "Není nastaven žádný aktivní ročník!"}
        )

    # C. Vytvoření objektu Víno
    nove_vino = Vino(
        nazev=nazev,
        odruda=odruda,
        barva=barva,
        sladkost=sladkost,
        privlastek=privlastek,
        rok_sklizne=rok_sklizne,
        vinar_id=user.id,           # ID přihlášeného vinaře
        rocnik_id=active_rocnik.id  # ID aktuálního ročníku
    )
    
    # D. Uložení do databáze
    db.add(nove_vino)
    db.commit()
    # db.refresh(nove_vino) # Není nutné, pokud hned přesměrováváme
    
    # E. Přesměrování zpět na seznam vín
    return RedirectResponse("/vina/sprava", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/upravit/{wine_id}")
def upravit_vino_page(
    wine_id: int,
    request: Request,
    ctx: dict = Depends(get_template_context),
    db: Session = Depends(get_db)
):
    # Kontrola prihlásenia
    if not ctx.get("user"):
        return RedirectResponse("/auth/login", status_code=303)
    
    # Načítanie užívateľa pre kontrolu oprávnení
    user = get_user_by_login(db, ctx["user"])
    
    # Nájdenie vína v databáze
    # Hľadáme podľa ID a zároveň kontrolujeme, či patrí prihlásenému vinárovi
    vino = db.query(Vino).filter(Vino.id == wine_id, Vino.vinar_id == user.id).first()
    
    if not vino:
        raise HTTPException(status_code=404, detail="Víno sa nenašlo alebo na jeho úpravu nemáte právo.")

    return ctx["request"].app.state.templates.TemplateResponse(
        "upravit_vino.html",
        {**ctx, "wine": vino} # Posielame objekt 'vino' do šablóny
    )

# 2. Uloženie zmien
@router.post("/upravit/{wine_id}")
def upravit_vino_submit(
    wine_id: int,
    request: Request,
    nazev: str = Form(...),      # Užívateľ zadáva názov ručne
    odruda: str = Form(...),
    barva: str = Form(...),
    sladkost: str = Form(None),
    privlastek: str = Form(None),
    rok_sklizne: int = Form(...),
    ctx: dict = Depends(get_template_context),
    db: Session = Depends(get_db)
):
    username = ctx.get("user")
    if not username:
        return RedirectResponse("/auth/login", status_code=303)
        
    user = get_user_by_login(db, username)
    
    # Opäť nájdeme víno a skontrolujeme vlastníka
    vino = db.query(Vino).filter(Vino.id == wine_id, Vino.vinar_id == user.id).first()
    
    if not vino:
        raise HTTPException(status_code=404, detail="Víno neexistuje.")

    # Aktualizácia atribútov
    vino.nazev = nazev
    vino.odruda = odruda
    vino.barva = barva
    vino.sladkost = sladkost
    vino.privlastek = privlastek
    vino.rok_sklizne = rok_sklizne
    
    db.commit() # Uloženie zmien do DB
    
    return RedirectResponse("/vina/sprava", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/smazat/{wine_id}")
def smazat_vino(
    wine_id: int,
    ctx: dict = Depends(get_template_context),
    db: Session = Depends(get_db)
):
    # 1. Kontrola přihlášení
    username = ctx.get("user")
    if not username:
        return RedirectResponse("/auth/login", status_code=303)
    
    user = get_user_by_login(db, username)
    
    # 2. Vyhledání vína + Kontrola vlastníka
    # Hledáme víno, které má dané ID a zároveň patří přihlášenému vinaři (vinar_id == user.id)
    vino = db.query(Vino).filter(Vino.id == wine_id, Vino.vinar_id == user.id).first()
    
    if not vino:
        # Pokud víno neexistuje nebo patří někomu jinému
        raise HTTPException(status_code=404, detail="Víno nenalezeno nebo nemáte oprávnění jej smazat.")
        
    # 3. Smazání z databáze
    db.delete(vino)
    db.commit()
    
    # 4. Přesměrování zpět na seznam
    return RedirectResponse("/vina/sprava", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/hodnoceni")
def hodnoceni_page(
    request: Request,
    ctx: dict = Depends(get_template_context),
    db: Session = Depends(get_db)
):
    # 1. Kontrola přihlášení
    username = ctx.get("user")
    if not username:
        return RedirectResponse("/auth/login", status_code=303)
    
    user = get_user_by_login(db, username)
    active_rocnik = get_aktivni_rocnik(db)
    
    if not active_rocnik:
         return ctx["request"].app.state.templates.TemplateResponse(
            "hodnoceni.html", {**ctx, "error": "Není aktivní ročník.", "wines_data": []}
        )

    # 2. Příprava dotazu
    # Chceme získat seznam cizích vín a k nim připojit hodnocení PŘIHLÁŠENÉHO uživatele (pokud existuje)
    MojeHodnoceni = aliased(Hodnoceni)

    results = (
        db.query(Vino, MojeHodnoceni)
        .join(Vino.vinar) # Abychom měli jméno vinaře
        .outerjoin(MojeHodnoceni, (MojeHodnoceni.vino_id == Vino.id) & (MojeHodnoceni.hodnotitel_id == user.id))
        .filter(Vino.rocnik_id == active_rocnik.id)
        .filter(Vino.vinar_id != user.id) # Filtr: Nezobrazovat vlastní vína
        .order_by(Vino.nazev)
        .all()
    )
    
    # 3. Transformace dat pro šablonu
    wines_data = []
    for vino, hodnoceni in results:
        wines_data.append({
            "vino": vino,
            "hodnoceni": hodnoceni # Objekt Hodnoceni nebo None
        })

    return ctx["request"].app.state.templates.TemplateResponse(
        "hodnoceni.html",
        {
            **ctx, 
            "wines_data": wines_data
        }
    )


@router.post("/hodnoceni")
async def hodnoceni_submit(
    request: Request,
    ctx: dict = Depends(get_template_context),
    db: Session = Depends(get_db)
):
    # 1. Kontrola přihlášení
    username = ctx.get("user")
    if not username:
        return RedirectResponse("/auth/login", status_code=303)
    
    user = get_user_by_login(db, username)
    
    # 2. Načtení všech dat z formuláře (raw data)
    form_data = await request.form()
    
    # 3. Iterace přes odeslaná data
    # Hledáme klíče ve formátu "body_{ID_VINA}", což nám identifikuje řádek tabulky
    for key, value in form_data.items():
        if key.startswith("body_"):
            try:
                # Získání ID vína a zadané hodnoty
                wine_id = int(key.split("_")[1])
                raw_body = value.strip()
                
                # Načtení poznámky ke stejnému vínu
                poznamka_key = f"poznamka_{wine_id}"
                poznamka_val = form_data.get(poznamka_key, "").strip()

                # Bezpečnostní kontrola: Opravdu víno nepatří hodnotiteli?
                vino_db = db.query(Vino).filter(Vino.id == wine_id).first()
                if not vino_db or vino_db.vinar_id == user.id:
                    continue

                # Hledání existujícího záznamu hodnocení v DB
                hodnoceni = db.query(Hodnoceni).filter(
                    Hodnoceni.vino_id == wine_id,
                    Hodnoceni.hodnotitel_id == user.id
                ).first()

                # --- Logika ukládání ---
                if raw_body:
                    # A) Uživatel zadal body -> Uložit nebo Aktualizovat
                    body_val = int(raw_body)
                    
                    # Ošetření rozsahu bodů (volitelné, HTML input to sice hlídá, ale backend je jistota)
                    if body_val < 0: body_val = 0
                    if body_val > 100: body_val = 100

                    if hodnoceni:
                        hodnoceni.body = body_val
                        hodnoceni.poznamka = poznamka_val
                    else:
                        nove_hodnoceni = Hodnoceni(
                            body=body_val,
                            poznamka=poznamka_val,
                            vino_id=wine_id,
                            hodnotitel_id=user.id
                        )
                        db.add(nove_hodnoceni)
                else:
                    # B) Políčko s body je prázdné -> Smazat hodnocení (pokud existovalo)
                    # To znamená, že uživatel hodnocení "vymazal"
                    if hodnoceni:
                        db.delete(hodnoceni)
                        
            except ValueError:
                # Pokud hodnota není číslo, přeskočíme
                continue

    # 4. Potvrzení všech změn najednou
    db.commit()
    
    # 5. Přesměrování zpět na tabulku
    return RedirectResponse("/vina/hodnoceni", status_code=status.HTTP_303_SEE_OTHER)