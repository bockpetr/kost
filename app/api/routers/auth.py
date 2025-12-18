from fastapi import APIRouter, Request, Form, Depends, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_password, create_access_token
from app.core.config import settings
from app.repositories.users import get_user_by_login
from app.dependencies import get_template_context

router = APIRouter()

@router.get("/login")
def login_page(
    request: Request,
    ctx: dict = Depends(get_template_context)
):
    """
    Zobrazí přihlašovací stránku.

    Vykreslí šablonu 'login.html' s předaným základním kontextem (např. menu,
    aktuální ročník, informace o aktuálním uživateli, pokud už je přihlášen).
    """
    return request.app.state.templates.TemplateResponse("login.html", {**ctx})

@router.post("/login")
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
    ctx: dict = Depends(get_template_context)
):
    """
    Zpracuje odeslaný přihlašovací formulář.

    Provede následující kroky:
    1. Ověří existenci uživatele podle loginu.
    2. Ověří správnost hesla (hash).
    3. Zkontroluje, zda má uživatel aktivní účet.
    4. V případě úspěchu vytvoří JWT access token.
    5. Nastaví token do zabezpečené HttpOnly cookie.
    6. Přesměruje uživatele na hlavní stránku.

    Pokud ověření selže, vrátí znovu přihlašovací formulář s chybovou hláškou.
    """
    user = get_user_by_login(db, username)
    
    if not user or not verify_password(password, user.password_hash):
        return request.app.state.templates.TemplateResponse(
            "login.html", 
            {**ctx, "error": "Neplatné jméno nebo heslo."}
        )
    
    if not user.is_active:
        return request.app.state.templates.TemplateResponse(
            "login.html", 
            {**ctx, "error": "Váš účet byl deaktivován."}
        )

    access_token = create_access_token(data={"sub": user.login})

    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    
    return response

@router.get("/logout")
def logout():
    """
    Odhlásí uživatele.

    Smaže cookie s přístupovým tokenem ('access_token')
    přesměruje uživatele na hlavní stránku.
    """
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("access_token")
    return response