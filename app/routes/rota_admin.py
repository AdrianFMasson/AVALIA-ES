from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlmodel import Session

from dependencies.dependencies import database
from dependencies.autenticacao import obter_usuario_autenticado
from config.Config import settings


admin_rota = APIRouter(tags=["Administrador"])

templates = Jinja2Templates(directory="templates")


def redirecionar_para_login():
    resposta = RedirectResponse(
        url="/login",
        status_code=status.HTTP_303_SEE_OTHER,
    )
    resposta.delete_cookie("access_token", path="/")
    return resposta


def exigir_admin(request: Request, db: Session):
    autenticacao = obter_usuario_autenticado(request, db)

    if autenticacao is None:
        return None

    if autenticacao["perfil"] != "ADMINISTRADOR":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seu perfil não tem permissão para acessar esta página.",
        )

    return autenticacao


@admin_rota.get("/dashboard-admin")
def dashboard_admin(
    request: Request,
    db: Session = Depends(database.get_db),
):
    autenticacao = exigir_admin(request, db)

    if autenticacao is None:
        return redirecionar_para_login()

    return templates.TemplateResponse(
        request=request,
        name="dashboard_admin.html",
        context={"usuario": autenticacao["usuario"]},
    )


@admin_rota.get("/config")
def config_admin(
    request: Request,
    db: Session = Depends(database.get_db),
):
    autenticacao = exigir_admin(request, db)

    if autenticacao is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticação necessária.",
        )

    return {
        "aplicacao": settings.model_dump(
            exclude={
                "ssh_password",
                "db_password",
                "JWT_SECRET_KEY",
            }
        ),
    }