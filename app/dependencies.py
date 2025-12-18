from fastapi import Request, Depends, Cookie, status, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from jose import jwt, JWTError

from app.core.config import settings
from app.core.database import get_db
from app.repositories.users import get_user_roles, get_user_by_login
from app.repositories.rocniky import get_vsechny_rocniky, get_aktivni_rocnik
from app.models.db import Users

def get_current_user_data(
    request: Request,
    access_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Získá základní data o přihlášeném uživateli z JWT tokenu v cookies.
    
    Tato funkce neblokuje přístup, pokud uživatel není přihlášen 
    (vrátí None v datech), což je vhodné pro veřejné stránky.

    Args:
        request: HTTP požadavek.
        access_token: JWT token získaný z cookie 'access_token'.
        db: Databázová relace.

    Returns:
        Dict: Slovník obsahující klíče 'user' (login) a 'roles' (seznam rolí).
    """
    user_info = {
        "user": None,
        "roles": []
    }
    
    if access_token:
        try:
            scheme, _, param = access_token.partition(" ")
            token_str = param if scheme.lower() == "bearer" else access_token
            
            payload = jwt.decode(token_str, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            username = payload.get("sub")
            
            if username:
                user_info["user"] = username
                user_info["roles"] = get_user_roles(db, username)
                
        except (JWTError, ValueError):
            pass
            
    return user_info

def get_template_context(
    request: Request,
    user_data: dict = Depends(get_current_user_data),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Připraví kontextová data, která jsou potřebná pro vykreslení šablon (Jinja2).
    
    Zahrnuje informace o aktuálním uživateli a ročnících, které se zobrazují
    v menu nebo hlavičce na každé stránce.

    Args:
        request: HTTP požadavek (nutný pro url_for v šablonách).
        user_data: Data uživatele z funkce get_current_user_data.
        db: Databázová relace.

    Returns:
        Dict: Kontext pro šablonu.
    """
    return {
        "request": request,
        "user": user_data["user"],
        "roles": user_data["roles"],
        "all_rocniky": get_vsechny_rocniky(db),
        "active_rocnik": get_aktivni_rocnik(db)
    }

def require_admin(user_data: dict = Depends(get_current_user_data)) -> dict:
    """
    Závislost, která vyžaduje, aby měl přihlášený uživatel roli 'Admin'.
    
    Pokud uživatel není admin, vyvolá výjimku 403 Forbidden.

    Args:
        user_data: Data uživatele.

    Raises:
        HTTPException: Pokud uživatel nemá roli Admin.

    Returns:
        dict: Data uživatele (pokud je admin).
    """
    if "Admin" not in user_data["roles"]:
        raise HTTPException(status_code=403, detail="Přístup odepřen")
    return user_data

def get_current_user(
    user_data: dict = Depends(get_current_user_data),
    db: Session = Depends(get_db)
) -> Users:
    """
    Získá plný ORM objekt aktuálně přihlášeného uživatele z databáze.
    
    Na rozdíl od get_current_user_data tato funkce VYŽADUJE přihlášení.
    Pokud uživatel není přihlášen nebo neexistuje, přesměruje na login.

    Args:
        user_data: Data z tokenu.
        db: Databázová relace.

    Raises:
        HTTPException: Přesměrování (303) na /auth/login, pokud autentizace selže.

    Returns:
        Users: Databázový objekt uživatele.
    """
    username = user_data.get("user")
    
    if not username:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/auth/login"} 
        )

    user = get_user_by_login(db, username)
    if not user:
         raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/auth/login"}
        )
    return user