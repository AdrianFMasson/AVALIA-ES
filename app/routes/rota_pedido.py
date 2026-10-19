from fastapi import APIRouter, Depends, Request, status, HTTPException
from entities.models import Pedido
from sqlmodel import Session
from sqlalchemy.exc import SQLAlchemyError
from dependencies.dependencies import database
from dependencies.autenticacao import obter_usuario_autenticado
from controller import PedidoController

pedido_rota = APIRouter()

PERFIS_CONSULTA = {"DISCENTE", "GESTOR", "ADMINISTRADOR"}
PERFIS_GERENCIAMENTO = {"GESTOR", "ADMINISTRADOR"}


def validar_perfil(request: Request, db: Session, perfis_autorizados: set):
    autenticacao = obter_usuario_autenticado(request, db)

    if autenticacao is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não autenticado ou sessão expirada."
        )

    if autenticacao["perfil"] not in perfis_autorizados:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seu perfil não tem permissão para executar esta operação."
        )

    return autenticacao


@pedido_rota.get("/pedido", status_code=status.HTTP_200_OK)
def buscar_pedidos(
    request: Request,
    db: Session = Depends(database.get_db)
):
    autenticacao = validar_perfil(request, db, PERFIS_CONSULTA)

    try:
        return PedidoController.buscar_pedidos(db)
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível consultar os pedidos."
        )


@pedido_rota.post(
    "/pedido",
    response_model=Pedido,
    status_code=status.HTTP_201_CREATED
)
def criar_pedido(
    dados: Pedido,
    request: Request,
    db: Session = Depends(database.get_db)
):
    validar_perfil(request, db, PERFIS_GERENCIAMENTO)

    try:
        return PedidoController.cadastrar_pedido(db, dados)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível cadastrar o pedido."
        )


@pedido_rota.put(
    "/pedido/{pedido_id}",
    response_model=Pedido
)
def atualizar_pedido(
    pedido_id: int,
    dados: Pedido,
    request: Request,
    db: Session = Depends(database.get_db)
):
    validar_perfil(request, db, PERFIS_GERENCIAMENTO)

    try:
        return PedidoController.atualizar_pedido(db, pedido_id, dados)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido não encontrado."
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível atualizar o pedido."
        )


@pedido_rota.delete(
    "/pedido/{pedido_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def deletar_pedido(
    pedido_id: int,
    request: Request,
    db: Session = Depends(database.get_db)
):
    validar_perfil(request, db, PERFIS_GERENCIAMENTO)

    try:
        PedidoController.deletar_pedido(db, pedido_id)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido não encontrado."
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível excluir o pedido."
        )