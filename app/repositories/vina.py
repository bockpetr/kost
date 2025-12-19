from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc
from typing import List, Tuple, Optional

from app.models.db import Vino, Hodnoceni, Users
from app.models.schemas import VinoCreate, VinoWithStats

def get_vina_by_rocnik(
    db: Session,
    rocnik_id: int
) -> List[VinoWithStats]:
    """
    Vrátí seznam vín pro daný ročník seřazený podle hodnocení.
    """
    vyber_vin = (
        db.query(
            Vino,
            func.avg(Hodnoceni.body).label("prumer_body"),
            func.count(Hodnoceni.id).label("pocet_hodnoceni")
        )
        .outerjoin(Vino.hodnoceni)
        .options(joinedload(Vino.vinar))
        .filter(Vino.rocnik_id == rocnik_id)
        .group_by(Vino.id)
        .order_by(desc("prumer_body"), Vino.nazev)
    )
    
    results = vyber_vin.all()
    
    hodnocena_vina = []
    for vino, avg, count in results:
        vino_dto = VinoWithStats.model_validate(vino)
        vino_dto.prumer_body = round(avg, 1) if avg else 0.0
        vino_dto.pocet_hodnoceni = count
        hodnocena_vina.append(vino_dto)
        
    return hodnocena_vina

def get_vino_detail(
    db: Session,
    vino_id: int
) -> Tuple[Optional[Vino], List[Hodnoceni]]:
    """
    Vrátí objekt vína a seznam hodnocení.
    """
    vino = (
        db.query(Vino)
        .options(
            joinedload(Vino.vinar),
            joinedload(Vino.hodnoceni).joinedload(Hodnoceni.hodnotitel)
        )
        .filter(Vino.id == vino_id)
        .first()
    )
    
    if not vino:
        return None, []
    
    sorted_ratings = sorted(vino.hodnoceni, key=lambda x: x.body or 0, reverse=True)
    
    return vino, sorted_ratings

def get_vina_by_vinar(
    db: Session,
    rocnik_id: int,
    vinar_id: int
) -> List[Vino]:
    """
    Vrátí vína konkrétního vinaře v daném ročníku.
    """
    return (
        db.query(Vino)
        .filter(Vino.rocnik_id == rocnik_id, Vino.vinar_id == vinar_id)
        .order_by(Vino.nazev)
        .all()
    )