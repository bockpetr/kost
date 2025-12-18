from fastapi import APIRouter, Request, Depends, status, HTTPException, Form    
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.dependencies import get_template_context, require_admin
from app.repositories.users import get_all_users, get_user_by_id, get_all_roles, get_user_by_login
from app.models.db import Role, Users
from app.core.security import get_password_hash

router = APIRouter()

@router.get("/profil")
def muj_profil_page(
    request: Request,
    ctx: dict = Depends(get_template_context),
    db: Session = Depends(get_db)
):

    username = ctx.get("user")
    if not username:
        return RedirectResponse("/auth/login", status_code=303)
    
    user = get_user_by_login(db, username)
    
    return ctx["request"].app.state.templates.TemplateResponse(
        "profil.html",
        {
            **ctx, 
            "profil_user": user
        }
    )

@router.post("/profil")
def muj_profil_submit(
    request: Request,
    jmeno: str = Form(...),
    email: str = Form(...),
    telefon: str = Form(None),
    adresa: str = Form(None),
    new_password: str = Form(None),
    password_confirm: str = Form(None),
    ctx: dict = Depends(get_template_context),
    db: Session = Depends(get_db)
):

    username = ctx.get("user")
    if not username:
        return RedirectResponse("/auth/login", status_code=303)
    
    user = get_user_by_login(db, username)
    
    user.jmeno = jmeno
    user.email = email
    user.telefon = telefon
    user.adresa = adresa
    
    error_msg = None
    if new_password:
        if new_password != password_confirm:
            error_msg = "Hesla se neshodují!"
        else:
            user.password_hash = get_password_hash(new_password)
            
    if error_msg:
        return ctx["request"].app.state.templates.TemplateResponse(
            "profil.html",
            {
                **ctx,
                "profil_user": user,
                "error": error_msg
            }
        )

    db.commit()
    
    return RedirectResponse("/users/profil", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/sprava")
def sprava_uzivatelu(
    request: Request,
    ctx: dict = Depends(get_template_context),
    db: Session = Depends(get_db),
    admin_check: dict = Depends(require_admin)
):
    
    users = get_all_users(db)

    return ctx["request"].app.state.templates.TemplateResponse(
        "sprava_uzivatelu.html",
        {
            **ctx, 
            "users": users
        }
    )

@router.get("/upravit/{user_id}")
def upravit_uzivatele_page(
    user_id: int,
    request: Request,
    ctx: dict = Depends(get_template_context),
    db: Session = Depends(get_db),
    admin_check: dict = Depends(require_admin)
):

    user_to_edit = get_user_by_id(db, user_id)
    all_roles = get_all_roles(db)
    
    if not user_to_edit:
        raise HTTPException(status_code=404, detail="Uživatel nenalezen")

    current_role_ids = [r.id for r in user_to_edit.role]

    return ctx["request"].app.state.templates.TemplateResponse(
        "upravit_uzivatele.html",
        {
            **ctx,
            "user_to_edit": user_to_edit,
            "all_roles": all_roles,
            "current_role_ids": current_role_ids
        }
    )

@router.post("/upravit/{user_id}")
def upravit_uzivatele_submit(
    user_id: int,
    request: Request,
    jmeno: str = Form(...),
    email: str = Form(...),
    telefon: str = Form(None),
    adresa: str = Form(None),
    is_active: bool = Form(False),
    roles: List[int] = Form([]),
    ctx: dict = Depends(get_template_context),
    db: Session = Depends(get_db),
    admin_check: dict = Depends(require_admin)
):

    user_to_edit = get_user_by_id(db, user_id)
    if not user_to_edit:
        raise HTTPException(status_code=404, detail="Uživatel nenalezen")

    user_to_edit.jmeno = jmeno
    user_to_edit.email = email
    user_to_edit.telefon = telefon
    user_to_edit.adresa = adresa

    current_user_login = ctx.get("user")
    
    if user_to_edit.login == current_user_login:
        user_to_edit.is_active = True
        pass
           
    else:
        user_to_edit.is_active = is_active
        new_roles = db.query(Role).filter(Role.id.in_(roles)).all()
        user_to_edit.role = new_roles

    db.commit()

    return RedirectResponse("/users/sprava", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/pridat")
def pridat_uzivatele_page(
    request: Request,
    ctx: dict = Depends(get_template_context),
    db: Session = Depends(get_db),
    admin_check: dict = Depends(require_admin)
):

    all_roles = get_all_roles(db)

    return ctx["request"].app.state.templates.TemplateResponse(
        "pridat_uzivatele.html",
        {**ctx, "all_roles": all_roles}
    )

@router.post("/pridat")
def pridat_uzivatele_submit(
    request: Request,
    login: str = Form(...),
    password: str = Form(...),
    jmeno: str = Form(...),
    email: str = Form(...),
    telefon: str = Form(None),
    adresa: str = Form(None),
    roles: List[int] = Form([]),
    ctx: dict = Depends(get_template_context),
    db: Session = Depends(get_db),
    admin_check: dict = Depends(require_admin)
):

    if get_user_by_login(db, login):
        all_roles = get_all_roles(db)
        return ctx["request"].app.state.templates.TemplateResponse(
            "pridat_uzivatele.html",
            {
                **ctx, 
                "all_roles": all_roles, 
                "error": f"Uživatel s loginem '{login}' už existuje!"
            }
        )
    
    hashed_pw = get_password_hash(password)

    new_user = Users(
        login=login,
        password_hash=hashed_pw,
        jmeno=jmeno,
        email=email,
        telefon=telefon,
        adresa=adresa,
        is_active=True
    )
    
    if roles:
        selected_roles = db.query(Role).filter(Role.id.in_(roles)).all()
        new_user.role = selected_roles

    db.add(new_user)
    db.commit()

    return RedirectResponse("/users/sprava", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/smazat/{user_id}")
def smazat_uzivatele(
    user_id: int,
    ctx: dict = Depends(get_template_context),
    db: Session = Depends(get_db),
    admin_check: dict = Depends(require_admin)
):

    current_user_login = ctx.get("user")
    current_user = get_user_by_login(db, current_user_login)
    
    user_to_delete = get_user_by_id(db, user_id)
    
    if not user_to_delete:
        return RedirectResponse("/users/sprava", status_code=status.HTTP_303_SEE_OTHER)

    if current_user.id == user_to_delete.id:
        users = get_all_users(db)
        return ctx["request"].app.state.templates.TemplateResponse(
            "sprava_uzivatele.html",
            {
                **ctx, 
                "users": users, 
                "error": "Nemůžete smazat svůj vlastní účet!"
            }
        )

    db.delete(user_to_delete)
    db.commit()
    
    return RedirectResponse("/users/sprava", status_code=status.HTTP_303_SEE_OTHER)