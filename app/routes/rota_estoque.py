from fastapi import APIRouter, Depends, Request, status, HTTPException
from entities.models import Estoque
from sqlmodel import Session
from dependencies.dependencies import database
from dependencies.autenticacao import obter_usuario_autenticado
from controller import EstoqueController

estoque_rota = APIRouter()

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


@estoque_rota.get(
    "/estoque",
    status_code=status.HTTP_200_OK
)
def buscar_estoques(
    request: Request,
    db: Session = Depends(database.get_db)
):
    validar_perfil(request, db, PERFIS_CONSULTA)

    try:
        return EstoqueController.buscar_estoques(db)
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível consultar o estoque."
        )


@estoque_rota.post(
    "/estoque",
    response_model=Estoque,
    status_code=status.HTTP_201_CREATED
)
def criar_estoque(
    dados: Estoque,
    request: Request,
    db: Session = Depends(database.get_db)
):
    validar_perfil(request, db, PERFIS_GERENCIAMENTO)

    try:
        return EstoqueController.cadastrar_estoque(db, dados)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível cadastrar o registro de estoque."
        )


@estoque_rota.put(
    "/estoque/{estoque_id}",
    response_model=Estoque
)
def atualizar_estoque(
    estoque_id: int,
    dados: Estoque,
    request: Request,
    db: Session = Depends(database.get_db)
):
    validar_perfil(request, db, PERFIS_GERENCIAMENTO)

    try:
        return EstoqueController.atualizar_estoque(
            db,
            estoque_id,
            dados
        )
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro de estoque não encontrado."
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível atualizar o registro de estoque."
        )


@estoque_rota.delete(
    "/estoque/{estoque_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def deletar_estoque(
    estoque_id: int,
    request: Request,
    db: Session = Depends(database.get_db)
):
    validar_perfil(request, db, PERFIS_GERENCIAMENTO)

    try:
        EstoqueController.deletar_estoque(db, estoque_id)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro de estoque não encontrado."
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível excluir o registro de estoque."
        )