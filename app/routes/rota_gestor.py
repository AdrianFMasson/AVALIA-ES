from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlmodel import Session

from dependencies.dependencies import database
from dependencies.autenticacao import obter_usuario_autenticado
from entities.models import Usuarios, Perfil


gestor_rota = APIRouter(tags=["Gestor"])

templates = Jinja2Templates(directory="templates")


def redirecionar_para_login():
    resposta = RedirectResponse(
        url="/login",
        status_code=status.HTTP_303_SEE_OTHER,
    )
    resposta.delete_cookie("access_token", path="/")
    return resposta


def exigir_gestor(request: Request, db: Session):
    autenticacao = obter_usuario_autenticado(request, db)

    if autenticacao is None:
        return None

    if autenticacao["perfil"] != "GESTOR":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seu perfil não tem permissão para acessar esta página.",
        )

    return autenticacao


@gestor_rota.get("/dashboard-gestor")
def dashboard_gestor(
    request: Request,
    db: Session = Depends(database.get_db),
):
    autenticacao = exigir_gestor(request, db)

    if autenticacao is None:
        return redirecionar_para_login()

    return templates.TemplateResponse(
        request=request,
        name="dashboard_gestor.html",
        context={"usuario": autenticacao["usuario"]},
    )


@gestor_rota.get("/gestor_users")
def gestor_users(
    request: Request,
    db: Session = Depends(database.get_db),
):
    autenticacao = exigir_gestor(request, db)

    if autenticacao is None:
        return redirecionar_para_login()

    return templates.TemplateResponse(
        request=request,
        name="gestor_users.html",
        context={"usuario": autenticacao["usuario"]},
    )


@gestor_rota.get("/gestor_equipamentos")
def gestor_equipamentos(
    request: Request,
    db: Session = Depends(database.get_db),
):
    autenticacao = exigir_gestor(request, db)

    if autenticacao is None:
        return redirecionar_para_login()

    return templates.TemplateResponse(
        request=request,
        name="gestor_equipamentos.html",
        context={"usuario": autenticacao["usuario"]},
    )


@gestor_rota.get("/gestor_pedidos")
def gestor_pedidos(
    request: Request,
    db: Session = Depends(database.get_db),
):
    autenticacao = exigir_gestor(request, db)

    if autenticacao is None:
        return redirecionar_para_login()

    return templates.TemplateResponse(
        request=request,
        name="gestor_pedidos.html",
        context={"usuario": autenticacao["usuario"]},
    )


@gestor_rota.get("/gestor/usuarios/editar/{usuario_id}")
def editar_usuario(
    usuario_id: int,
    request: Request,
    db: Session = Depends(database.get_db),
):
    autenticacao = exigir_gestor(request, db)

    if autenticacao is None:
        return redirecionar_para_login()

    usuario = db.get(Usuarios, usuario_id)

    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado.",
        )

    perfil = db.get(Perfil, usuario.id_perfil)

    if perfil is None or perfil.perfil.value != "DISCENTE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Somente usuários com perfil DISCENTE podem ser editados nesta página.",
        )

    return templates.TemplateResponse(
        request=request,
        name="gestor_users_editar.html",
        context={
            "usuario": autenticacao["usuario"],
            "discente": usuario,
        },
    )


@gestor_rota.get("/gestor/pedidos/editar/{pedido_id}")
def gestor_pedidos_editar(
    pedido_id: int,
    request: Request,
    db: Session = Depends(database.get_db),
):
    autenticacao = exigir_gestor(request, db)

    if autenticacao is None:
        return redirecionar_para_login()

    return templates.TemplateResponse(
        request=request,
        name="gestor_pedidos_editar.html",
        context={
            "usuario": autenticacao["usuario"],
            "pedido_id": pedido_id,
        },
    )