from fastapi import APIRouter, Depends, Request, status, HTTPException
from entities.models import Emprestimos
from sqlmodel import Session
from dependencies.dependencies import database
from controller import EmprestimosController
from dependencies.autenticacao import obter_usuario_autenticado

emprestimos_rota = APIRouter()

PERFIS_AUTORIZADOS = {"DISCENTE", "GESTOR", "ADMINISTRADOR"}


def validar_acesso_emprestimos(
    request: Request,
    db: Session
):
    autenticacao = obter_usuario_autenticado(request, db)

    if autenticacao is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não autenticado ou sessão expirada."
        )

    usuario = autenticacao.get("usuario")
    perfil = autenticacao.get("perfil")

    if usuario is None or not usuario.ativo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário inexistente ou inativo."
        )

    if perfil not in PERFIS_AUTORIZADOS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seu perfil não tem permissão para acessar os empréstimos."
        )

    return {
        "usuario": usuario,
        "perfil": perfil
    }


@emprestimos_rota.get(
    "/emprestimos",
    status_code=status.HTTP_200_OK
)
def buscar_emprestimos(
    request: Request,
    db: Session = Depends(database.get_db)
):
    validar_acesso_emprestimos(request, db)

    try:
        return EmprestimosController.buscar_emprestimos(db)
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível consultar os empréstimos."
        )


@emprestimos_rota.post(
    "/emprestimos",
    response_model=Emprestimos,
    status_code=status.HTTP_201_CREATED
)
def criar_emprestimo(
    dados: Emprestimos,
    request: Request,
    db: Session = Depends(database.get_db)
):
    validar_acesso_emprestimos(request, db)

    try:
        return EmprestimosController.cadastrar_emprestimo(db, dados)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível cadastrar o empréstimo."
        )


@emprestimos_rota.put(
    "/emprestimos/{emprestimo_id}",
    response_model=Emprestimos
)
def atualizar_emprestimo(
    emprestimo_id: int,
    dados: Emprestimos,
    request: Request,
    db: Session = Depends(database.get_db)
):
    validar_acesso_emprestimos(request, db)

    try:
        return EmprestimosController.atualizar_emprestimo(
            db,
            emprestimo_id,
            dados
        )
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empréstimo não encontrado."
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível atualizar o empréstimo."
        )


@emprestimos_rota.delete(
    "/emprestimos/{emprestimo_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def deletar_emprestimo(
    emprestimo_id: int,
    request: Request,
    db: Session = Depends(database.get_db)
):
    validar_acesso_emprestimos(request, db)

    try:
        EmprestimosController.deletar_emprestimo(db, emprestimo_id)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empréstimo não encontrado."
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível excluir o empréstimo."
        )