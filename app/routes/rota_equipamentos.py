from fastapi import APIRouter, Depends, Request, status, HTTPException
from entities.models import Equipamentos, EquipamentoPublico
from sqlmodel import Session
from dependencies.dependencies import database
from dependencies.autenticacao import obter_usuario_autenticado
from controller import EquipamentosController

equipamentos_rota = APIRouter()

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


@equipamentos_rota.get(
    "/equipamentos",
    status_code=status.HTTP_200_OK
)
def buscar_equipamentos(
    request: Request,
    db: Session = Depends(database.get_db)
):
    validar_perfil(request, db, PERFIS_CONSULTA)

    try:
        return EquipamentosController.buscar_equipamentos(db)
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível consultar os equipamentos."
        )


@equipamentos_rota.post(
    "/equipamentos",
    response_model=Equipamentos,
    status_code=status.HTTP_201_CREATED
)
def criar_equipamento(
    dados: Equipamentos,
    request: Request,
    db: Session = Depends(database.get_db)
):
    validar_perfil(request, db, PERFIS_GERENCIAMENTO)

    try:
        return EquipamentosController.cadastrar_equipamento(db, dados)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível cadastrar o equipamento."
        )


@equipamentos_rota.put(
    "/equipamentos/{equipamento_id}",
    response_model=Equipamentos
)
def atualizar_equipamento(
    equipamento_id: int,
    dados: EquipamentoPublico,
    request: Request,
    db: Session = Depends(database.get_db)
):
    validar_perfil(request, db, PERFIS_GERENCIAMENTO)

    try:
        return EquipamentosController.atualizar_equipamento(
            db,
            equipamento_id,
            dados
        )
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipamento não encontrado."
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível atualizar o equipamento."
        )


@equipamentos_rota.delete(
    "/equipamentos/{equipamento_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def deletar_equipamento(
    equipamento_id: int,
    request: Request,
    db: Session = Depends(database.get_db)
):
    validar_perfil(request, db, PERFIS_GERENCIAMENTO)

    try:
        EquipamentosController.deletar_equipamento(db, equipamento_id)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipamento não encontrado."
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível excluir o equipamento."
        )