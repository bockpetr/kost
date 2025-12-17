from fastapi import APIRouter, Request, Form, Depends, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.users import get_user_by_login
from app.core.security import verify_password, create_access_token
from app.dependencies import get_template_context

router = APIRouter()

@router.get("/login")
def login_page(
    request: Request,
    ctx: dict = Depends(get_template_context)
):
    return request.app.state.templates.TemplateResponse("login.html", {**ctx})

@router.post("/login")
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
    ctx: dict = Depends(get_template_context)
):

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
        max_age=1800
    )
    
    return response

@router.get("/logout")
def logout():
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("access_token")
    return response