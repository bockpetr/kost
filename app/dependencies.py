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
    Pokud je uživatel přihlášen vrací jeho login a role.
    Pokud není uživatel přihlášen vrací prázdná data.
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
    Připraví globální data (kontext) pro šablony Jinja2.
    Tato funkce se volá na téměř každé stránce. Zajišťuje, že šablona 'base.html'
    má vždy přístup k:
    1. Objektu Request (nutný pro generování URL).
    2. Informacím o uživateli.
    3. Seznamu ročníků (pro vykreslení navigačního menu).
    4. Informaci o tom, který ročník je právě aktivní.
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
    Bezpečnostní závislost pro ochranu administrátorských sekcí.
    Zkontroluje, zda má aktuální uživatel roli 'Admin'.
    Pokud ne, okamžitě ukončí požadavek chybou 403 Forbidden.
    """
    if "Admin" not in user_data["roles"]:
        raise HTTPException(status_code=403, detail="Přístup odepřen")
    return user_data

def get_current_user(
    user_data: dict = Depends(get_current_user_data),
    db: Session = Depends(get_db)
) -> Users:
    """
    Získá plný databázový objekt aktuálně přihlášeného uživatele.
    Pokud uživatel není přihlášen (token je neplatný nebo vypršel), 
    automaticky ho přesměruje na přihlašovací stránku (/auth/login).
    Nutné pro kontrolu přístupu do neveřejných sekcí.
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