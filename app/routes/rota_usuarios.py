from fastapi import APIRouter, Depends, Request, status, HTTPException
from entities.models import Usuarios, UsuarioAtualizacao
from sqlmodel import Session
from dependencies.dependencies import database
from dependencies.autenticacao import obter_usuario_autenticado
from controller import UsuariosController

usuarios_rota = APIRouter()

PERFIS_GERENCIAMENTO = {"GESTOR", "ADMINISTRADOR"}


def validar_autenticacao(request: Request, db: Session):
    autenticacao = obter_usuario_autenticado(request, db)

    if autenticacao is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não autenticado ou sessão expirada."
        )

    return autenticacao


def validar_gerenciamento(request: Request, db: Session):
    autenticacao = validar_autenticacao(request, db)

    if autenticacao["perfil"] not in PERFIS_GERENCIAMENTO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seu perfil não tem permissão para gerenciar usuários."
        )

    return autenticacao


@usuarios_rota.get(
    "/usuarios",
    response_model=list[Usuarios],
    status_code=status.HTTP_200_OK
)
def buscar_usuarios(
    request: Request,
    db: Session = Depends(database.get_db)
):
    # Valida se o usuário logado possui perfil de Gestor ou Administrador
    validar_gerenciamento(request, db)

    try:
        # Nota: Certifique-se de que o método no seu controller chame algo como 'listar_usuarios' 
        # ou 'buscar_todos_usuarios'. Altere o nome abaixo se o seu método tiver outra nomenclatura.
        return UsuariosController.listar_usuarios(db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@usuarios_rota.post(
    "/usuarios",
    response_model=Usuarios,
    status_code=status.HTTP_201_CREATED
)
def criar_usuario(
    dados: Usuarios,
    request: Request,
    db: Session = Depends(database.get_db)
):
    validar_gerenciamento(request, db)

    try:
        return UsuariosController.cadastrar_usuario(db, dados)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@usuarios_rota.put(
    "/usuarios/{usuario_id}",
    response_model=Usuarios
)
def atualizar_usuario(
    usuario_id: int,
    dados: UsuarioAtualizacao,
    request: Request,
    db: Session = Depends(database.get_db)
):
    autenticacao = validar_gerenciamento(request, db)

    try:
        if autenticacao["perfil"] == "GESTOR":
            usuario_atualizado = UsuariosController.buscar_usuario_por_id(
                db,
                usuario_id
            )

            if usuario_atualizado.id_perfil != 1:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="O gestor só pode atualizar usuários discentes."
                )

        return UsuariosController.atualizar_usuario(
            db,
            usuario_id,
            dados
        )
    except HTTPException:
        raise
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@usuarios_rota.delete(
    "/usuarios/{usuario_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def deletar_usuario(
    usuario_id: int,
    request: Request,
    db: Session = Depends(database.get_db)
):
    validar_gerenciamento(request, db)

    try:
        UsuariosController.deletar_usuario(db, usuario_id)
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )