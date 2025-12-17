from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.db import Users, Role

def get_user_by_login(db: Session, login: str) -> Optional[Users]:
    return db.query(Users).filter(Users.login == login).first()

def get_user_roles(db: Session, login: str)-> List[str]:
    user = get_user_by_login(db, login)
    if user:
        return [role.nazev for role in user.role]
    return []

def get_public_user_detail(db: Session, user_id: int):
    return db.query(Users).filter(Users.id == user_id).first()

def get_all_users(db: Session) -> List[Users]:
    """Vrátí seznam všech uživatelů seřazený podle ID."""
    return db.query(Users).order_by(Users.id).all()

def get_user_by_id(db: Session, user_id: int) -> Optional[Users]:
    return db.query(Users).filter(Users.id == user_id).first()

def get_all_roles(db: Session) -> List[Role]:
    return db.query(Role).all()