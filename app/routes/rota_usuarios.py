
import logging

from fastapi import APIRouter, Depends, Request, status, HTTPException
from sqlmodel import Session

from entities.models import Usuarios, UsuarioAtualizacao
from dependencies.dependencies import database
from dependencies.autenticacao import obter_usuario_autenticado
from controller import UsuariosController


logger = logging.getLogger(__name__)

usuarios_rota = APIRouter()

PERFIS_GERENCIAMENTO = {"GESTOR", "ADMINISTRADOR"}

# Confirme se o ID 1 corresponde a DISCENTE no seu banco de dados.
ID_PERFIL_DISCENTE = 1


def validar_autenticacao(
    request: Request,
    db: Session,
) -> dict:
    autenticacao = obter_usuario_autenticado(request, db)

    if autenticacao is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não autenticado ou sessão expirada.",
        )

    return autenticacao


def validar_gerenciamento(
    request: Request,
    db: Session,
) -> dict:
    autenticacao = validar_autenticacao(request, db)

    if autenticacao["perfil"] not in PERFIS_GERENCIAMENTO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seu perfil não tem permissão para gerenciar usuários.",
        )

    return autenticacao


@usuarios_rota.get(
    "/usuarios",
    response_model=list[Usuarios],
    status_code=status.HTTP_200_OK,
)
def buscar_usuarios(
    request: Request,
    db: Session = Depends(database.get_db),
):
    validar_gerenciamento(request, db)

    try:
        return UsuariosController.buscar_usuarios(db)

    except HTTPException:
        raise

    except Exception:
        logger.exception("Erro ao consultar usuários.")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Não foi possível consultar os usuários.",
        )


@usuarios_rota.post(
    "/usuarios",
    response_model=Usuarios,
    status_code=status.HTTP_201_CREATED,
)
def criar_usuario(
    dados: Usuarios,
    request: Request,
    db: Session = Depends(database.get_db),
):
    autenticacao = validar_gerenciamento(request, db)

    try:
        # O gestor só pode cadastrar discentes.
        if (
            autenticacao["perfil"] == "GESTOR"
            and dados.id_perfil != ID_PERFIL_DISCENTE
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="O gestor só pode cadastrar usuários discentes.",
            )

        return UsuariosController.cadastrar_usuario(db, dados)

    except HTTPException:
        raise

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    except RuntimeError:
        logger.exception("Erro ao cadastrar usuário.")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Não foi possível cadastrar o usuário.",
        )


@usuarios_rota.put(
    "/usuarios/{usuario_id}",
    response_model=Usuarios,
    status_code=status.HTTP_200_OK,
)
def atualizar_usuario(
    usuario_id: int,
    dados: UsuarioAtualizacao,
    request: Request,
    db: Session = Depends(database.get_db),
):
    autenticacao = validar_gerenciamento(request, db)

    try:
        # O gestor só pode editar usuários discentes.
        if autenticacao["perfil"] == "GESTOR":
            usuario_alvo = UsuariosController.buscar_usuario_por_id(
                db,
                usuario_id,
            )

            if usuario_alvo is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Usuário não encontrado.",
                )

            if usuario_alvo.id_perfil != ID_PERFIL_DISCENTE:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="O gestor só pode atualizar usuários discentes.",
                )

            # Impede que o gestor transforme um discente em outro perfil.
            if dados.id_perfil != ID_PERFIL_DISCENTE:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="O gestor não pode alterar o perfil do discente.",
                )

        return UsuariosController.atualizar_usuario(
            db,
            usuario_id,
            dados,
        )

    except HTTPException:
        raise

    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado.",
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    except RuntimeError:
        logger.exception("Erro ao atualizar usuário.")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Não foi possível atualizar o usuário.",
        )


@usuarios_rota.delete(
    "/usuarios/{usuario_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def deletar_usuario(
    usuario_id: int,
    request: Request,
    db: Session = Depends(database.get_db),
):
    autenticacao = validar_gerenciamento(request, db)

    # Somente administradores podem excluir usuários.
    if autenticacao["perfil"] != "ADMINISTRADOR":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Somente administradores podem excluir usuários.",
        )

    try:
        UsuariosController.deletar_usuario(db, usuario_id)

    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado.",
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    except RuntimeError:
        logger.exception("Erro ao excluir usuário.")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Não foi possível excluir o usuário.",
        )
