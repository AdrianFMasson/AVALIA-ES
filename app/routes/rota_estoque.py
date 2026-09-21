from fastapi import APIRouter, Depends, status, HTTPException

from entities.models import Estoque

from sqlmodel import Session

from dependencies.dependencies import database

from controller import EstoqueController


estoque_rota = APIRouter()


@estoque_rota.get(
    "/estoque",
    status_code=status.HTTP_200_OK
)
def buscar_estoques(
    db: Session = Depends(database.get_db)
):
    try:
        estoques = EstoqueController.buscar_estoques(db)

        return estoques

    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@estoque_rota.post(
    "/estoque",
    response_model=Estoque,
    status_code=status.HTTP_201_CREATED
)
def criar_estoque(
    dados: Estoque,
    db: Session = Depends(database.get_db)
):
    try:
        return EstoqueController.cadastrar_estoque(
            db,
            dados
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


@estoque_rota.put(
    "/estoque/{estoque_id}",
    response_model=Estoque
)
def atualizar_estoque(
    estoque_id: int,
    dados: Estoque,
    db: Session = Depends(database.get_db)
):
    try:
        return EstoqueController.atualizar_estoque(
            db,
            estoque_id,
            dados
        )

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


@estoque_rota.delete(
    "/estoque/{estoque_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def deletar_estoque(
    estoque_id: int,
    db: Session = Depends(database.get_db)
):
    try:
        EstoqueController.deletar_estoque(
            db,
            estoque_id
        )

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