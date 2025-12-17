from sqlalchemy.orm import Session
from app.models.db import Rocnik
from typing import List, Optional

def get_aktivni_rocnik(db: Session) -> Optional[Rocnik]:
    """Vrátí aktuálně aktivní ročník."""
    return db.query(Rocnik).filter(Rocnik.is_active == True).first()

def get_vsechny_rocniky(db: Session) -> List[Rocnik]:
    """Vrátí všechny ročníky seřazené sestupně (nejnovější nahoře)."""
    return db.query(Rocnik).order_by(Rocnik.rok.desc()).all()

def get_rocnik_by_id(db: Session, rocnik_id: int) -> Optional[Rocnik]:
    """Najde ročník podle ID."""
    return db.query(Rocnik).filter(Rocnik.id == rocnik_id).first()

def get_nejnovejsi_rocnik(db: Session) -> Optional[Rocnik]:
    """Vrátí ročník s nejvyšším letopočtem (pro kontrolu aktivace)."""
    return db.query(Rocnik).order_by(Rocnik.rok.desc()).first()

def set_active_rocnik_logic(db: Session, rocnik_id: int):
    """
    Nastaví vybraný ročník jako aktivní a VŠECHNY ostatní deaktivuje.
    """
    # 1. Deaktivovat vše
    db.query(Rocnik).update({Rocnik.is_active: False})
    
    # 2. Aktivovat vybraný
    rocnik = db.query(Rocnik).filter(Rocnik.id == rocnik_id).first()
    if rocnik:
        rocnik.is_active = True
    
    db.commit()

def deactivate_rocnik_logic(db: Session, rocnik_id: int):
    """
    Pouze deaktivuje daný ročník. Žádný jiný se neaktivuje.
    Výsledkem je stav, kdy žádný ročník není aktivní.
    """
    rocnik = db.query(Rocnik).filter(Rocnik.id == rocnik_id).first()
    if rocnik:
        rocnik.is_active = False
        db.commit()