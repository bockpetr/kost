from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc
from typing import List, Tuple, Optional

from app.models.db import Vino, Hodnoceni, Users
from app.models.schemas import VinoCreate, VinoWithStats

def get_wines_by_rocnik(db: Session, rocnik_id: int):
    """
    Vrátí seznam vín pro daný ročník seřazený podle hodnocení.
    Vrací seznam Pydantic modelů VinoWithStats.
    """
    # Dotaz: Vybereme Víno a k němu průměr bodů a počet hodnocení
    query = (
        db.query(
            Vino,
            func.avg(Hodnoceni.body).label("prumer_body"),
            func.count(Hodnoceni.id).label("pocet_hodnoceni")
        )
        .outerjoin(Hodnoceni) # Levé spojení, abychom měli i nehodnocená vína
        .options(joinedload(Vino.vinar))
        .filter(Vino.rocnik_id == rocnik_id)
        .group_by(Vino.id)
        .order_by(desc("prumer_body"), Vino.nazev)
    )
    
    results = query.all()
    
    # ORM vrací n-tice (Vino, prumer, pocet). 
    # Abychom nerozbili šablonu, můžeme to "obejít" a hodnoty přilepit k objektu,
    # nebo vrátit upravený seznam slovníků.
    # Zde je trik, jak vrátit objekt vína, který má navíc atribut 'prumer_body':
    enriched_wines = []
    for wine, avg, count in results:
        wine_dto = VinoWithStats.model_validate(wine)
        wine_dto.prumer_body = round(avg, 1) if avg else 0.0
        wine_dto.pocet_hodnoceni = count
        enriched_wines.append(wine_dto)
        
    return enriched_wines

def get_wine_detail(db: Session, wine_id: int):
    """
    Vrátí objekt vína a seznam hodnocení.
    Díky ORM už 'wine' obsahuje seznam 'hodnoceni' i objekt 'vinar'.
    """
    # Použijeme joinedload, abychom načetli vinaře i hodnocení jedním dotazem (optimalizace)
    wine = (
        db.query(Vino)
        .options(
            joinedload(Vino.vinar),      # Načti vinaře
            joinedload(Vino.hodnoceni).joinedload(Hodnoceni.hodnotitel) # Načti hodnocení a k nim hodnotitele
        )
        .filter(Vino.id == wine_id)
        .first()
    )
    
    if not wine:
        return None, []
    
    # ORM relace wine.hodnoceni je seznam objektů Hodnoceni
    # Seřadíme hodnocení podle bodů (v Pythonu)
    sorted_ratings = sorted(wine.hodnoceni, key=lambda x: x.body or 0, reverse=True)
    
    return wine, sorted_ratings

def get_wines_by_vinar(db: Session, rocnik_id: int, vinar_id: int):
    """
    Vrátí vína konkrétního vinaře v daném ročníku.
    """
    return (
        db.query(Vino)
        .filter(Vino.rocnik_id == rocnik_id, Vino.vinar_id == vinar_id)
        .order_by(Vino.nazev)
        .all()
    )