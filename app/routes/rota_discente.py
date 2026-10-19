from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlmodel import Session
from sqlalchemy.exc import SQLAlchemyError

from dependencies.dependencies import database
from dependencies.autenticacao import (
    obter_usuario_autenticado,
)
from controller import EmprestimosController


discente_rota = APIRouter(
    tags=["Discente"],
)

templates = Jinja2Templates(directory="templates")


def redirecionar_para_login():
    resposta = RedirectResponse(
        url="/login",
        status_code=status.HTTP_303_SEE_OTHER,
    )
    resposta.delete_cookie("access_token", path="/")

    resposta.headers["Cache-Control"] = (
        "no-store, no-cache, must-revalidate, private, max-age=0"
    )
    resposta.headers["Pragma"] = "no-cache"
    resposta.headers["Expires"] = "0"

    return resposta


def exigir_discente(
    request: Request,
    db: Session,
):
    autenticacao = obter_usuario_autenticado(request, db)

    if autenticacao is None:
        return None

    if autenticacao["perfil"] != "DISCENTE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seu perfil não tem permissão para acessar esta página.",
        )

    return autenticacao


@discente_rota.get("/dashboard-user")
def dashboard_user(
    request: Request,
    db: Session = Depends(database.get_db),
):
    autenticacao = exigir_discente(request, db)

    if autenticacao is None:
        return redirecionar_para_login()

    resposta = templates.TemplateResponse(
        request=request,
        name="dashboard_user.html",
        context={
            "usuario": autenticacao["usuario"],
        },
    )

    return resposta


@discente_rota.get("/user_pedidos")
def user_pedidos(
    request: Request,
    db: Session = Depends(database.get_db),
):
    autenticacao = exigir_discente(request, db)

    if autenticacao is None:
        return redirecionar_para_login()

    resposta = templates.TemplateResponse(
        request=request,
        name="user_pedidos.html",
        context={
            "usuario": autenticacao["usuario"],
        },
    )

    return resposta


@discente_rota.get("/user_emprestimos")
def user_emprestimos(
    request: Request,
    db: Session = Depends(database.get_db),
):
    autenticacao = exigir_discente(request, db)

    if autenticacao is None:
        return redirecionar_para_login()

    usuario = autenticacao["usuario"]

    try:
        emprestimos = (
            EmprestimosController.buscar_emprestimos_usuario(
                db,
                usuario.id_usuario,
            )
        )

    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível consultar seus empréstimos. Tente novamente.",
        )

    resposta = templates.TemplateResponse(
        request=request,
        name="user_emprestimos.html",
        context={
            "usuario": usuario,
            "emprestimos": emprestimos,
        },
    )

    return resposta


@discente_rota.get("/user_perfil")
def user_perfil(
    request: Request,
    db: Session = Depends(database.get_db),
):
    autenticacao = exigir_discente(request, db)

    if autenticacao is None:
        return redirecionar_para_login()

    resposta = templates.TemplateResponse(
        request=request,
        name="user_perfil.html",
        context={
            "usuario": autenticacao["usuario"],
        },
    )

    return resposta