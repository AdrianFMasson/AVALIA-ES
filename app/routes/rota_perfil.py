import logging

from fastapi import APIRouter, Depends, Request, status, HTTPException
from sqlmodel import Session

from entities.models import Perfil
from dependencies.dependencies import database
from dependencies.autenticacao import obter_usuario_autenticado
from controller import PerfilController


perfil_rota = APIRouter()
logger = logging.getLogger(__name__)

PERFIS_GERENCIAMENTO = {"GESTOR", "ADMINISTRADOR"}


def validar_autenticacao(request: Request, db: Session):
    autenticacao = obter_usuario_autenticado(request, db)

    if autenticacao is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não autenticado ou sessão expirada.",
        )

    return autenticacao


def validar_gerenciamento(request: Request, db: Session):
    autenticacao = validar_autenticacao(request, db)

    perfil = str(autenticacao["perfil"]).strip().upper()

    if perfil not in PERFIS_GERENCIAMENTO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Somente gestores e administradores podem consultar os perfis.",
        )

    return autenticacao


def validar_administrador(request: Request, db: Session):
    autenticacao = validar_autenticacao(request, db)

    perfil = str(autenticacao["perfil"]).strip().upper()

    if perfil != "ADMINISTRADOR":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Somente administradores podem gerenciar perfis.",
        )

    return autenticacao


@perfil_rota.get(
    "/perfil",
    response_model=list[Perfil],
    status_code=status.HTTP_200_OK,
)
def buscar_perfis(
    request: Request,
    db: Session = Depends(database.get_db),
):
    validar_gerenciamento(request, db)

    try:
        return PerfilController.buscar_perfis(db)
    except HTTPException:
        raise
    except RuntimeError:
        logger.exception("Erro ao consultar perfis.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível consultar os perfis.",
        )


@perfil_rota.post(
    "/perfil",
    response_model=Perfil,
    status_code=status.HTTP_201_CREATED,
)
def criar_perfil(
    dados: Perfil,
    request: Request,
    db: Session = Depends(database.get_db),
):
    validar_administrador(request, db)

    try:
        return PerfilController.cadastrar_perfil(db, dados)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except RuntimeError:
        logger.exception("Erro ao cadastrar perfil.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível cadastrar o perfil.",
        )


@perfil_rota.put(
    "/perfil/{perfil_id}",
    response_model=Perfil,
    status_code=status.HTTP_200_OK,
)
def atualizar_perfil(
    perfil_id: int,
    dados: Perfil,
    request: Request,
    db: Session = Depends(database.get_db),
):
    validar_administrador(request, db)

    try:
        return PerfilController.atualizar_perfil(db, perfil_id, dados)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil não encontrado.",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except RuntimeError:
        logger.exception("Erro ao atualizar perfil.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível atualizar o perfil.",
        )


@perfil_rota.delete(
    "/perfil/{perfil_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def deletar_perfil(
    perfil_id: int,
    request: Request,
    db: Session = Depends(database.get_db),
):
    validar_administrador(request, db)

    try:
        PerfilController.deletar_perfil(db, perfil_id)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil não encontrado.",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except RuntimeError:
        logger.exception("Erro ao excluir perfil.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível excluir o perfil.",
        )