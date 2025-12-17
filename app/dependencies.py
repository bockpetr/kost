from fastapi import Request, Depends, Cookie, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from jose import jwt, JWTError

from app.core.config import settings
from app.core.database import get_db
from app.repositories.users import get_user_roles
from app.repositories.rocniky import get_vsechny_rocniky, get_aktivni_rocnik

# 1. Získání přihlášeného uživatele (Auth)
# Tato funkce se postará o parsování cookie a ověření tokenu
def get_current_user_data(
    request: Request,
    access_token: Optional[str] = Cookie(None), # FastAPI samo vytáhne cookie 'access_token'
    db: Session = Depends(get_db)               # Automaticky získá DB session (thread-safe)
):
    user_info = {
        "user": None,
        "roles": []
    }
    
    if access_token:
        try:
            # Ošetření prefixu "Bearer " (pokud tam je)
            scheme, _, param = access_token.partition(" ")
            token_str = param if scheme.lower() == "bearer" else access_token
            
            # Dekódování JWT
            payload = jwt.decode(token_str, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            username = payload.get("sub")
            
            if username:
                user_info["user"] = username
                user_info["roles"] = get_user_roles(db, username)
                
        except (JWTError, ValueError):
            # Token je neplatný nebo vypršel -> uživatel zůstane nepřihlášen
            pass
            
    return user_info

# 2. Kontext pro šablony (Global Template Context)
# Protože jsme zrušili middleware, musíme routerům nějak předat data pro menu (ročníky, user).
# Tato dependency to udělá za nás.
def get_template_context(
    request: Request,
    user_data: dict = Depends(get_current_user_data),
    db: Session = Depends(get_db)
):
    return {
        "request": request,
        "user": user_data["user"],      # Do šablony půjde rovnou {{ user }}
        "roles": user_data["roles"],
        "all_rocniky": get_vsechny_rocniky(db),
        "active_rocnik": get_aktivni_rocnik(db)
    }

def require_admin(user_data: dict = Depends(get_current_user_data)):
    if "Admin" not in user_data["roles"]:
        raise HTTPException(status_code=403, detail="Přístup odepřen")
    return user_data