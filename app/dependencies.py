from fastapi import Request, Depends, Cookie, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from jose import jwt, JWTError

from app.core.config import settings
from app.core.database import get_db
from app.repositories.users import get_user_roles, get_user_by_login
from app.repositories.rocniky import get_vsechny_rocniky, get_aktivni_rocnik

def get_current_user_data(
    request: Request,
    access_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
):
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
):
    return {
        "request": request,
        "user": user_data["user"],
        "roles": user_data["roles"],
        "all_rocniky": get_vsechny_rocniky(db),
        "active_rocnik": get_aktivni_rocnik(db)
    }

def require_admin(user_data: dict = Depends(get_current_user_data)):
    if "Admin" not in user_data["roles"]:
        raise HTTPException(status_code=403, detail="Přístup odepřen")
    return user_data

def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
):
    username = request.session.get("user")
    if not username:
        raise HTTPException(status_code=303, detail="/auth/login")

    user = get_user_by_login(db, username)
    return user