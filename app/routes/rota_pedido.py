from fastapi import APIRouter, Depends, status, HTTPException
from entities.models import Pedido
from sqlmodel import Session
from dependencies.dependencies import database
from controller import PedidoController

pedido_rota = APIRouter()

@pedido_rota.get("/pedido", status_code=status.HTTP_200_OK)
def buscar_pedidos(db: Session = Depends(database.get_db)):
    try:
        pedidos = PedidoController.buscar_pedidos(db)
        return pedidos
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@pedido_rota.post("/pedido",
    response_model=Pedido,
    status_code=status.HTTP_201_CREATED)
def criar_pedido(dados: Pedido, db: Session = Depends(database.get_db)):
    try:
        return PedidoController.cadastrar_pedido(db, dados)
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

@pedido_rota.put("/pedido/{pedido_id}", response_model=Pedido)
def atualizar_pedido(pedido_id: int, dados: Pedido, db: Session = Depends(database.get_db)):
    try:
        return PedidoController.atualizar_pedido(db, pedido_id, dados)
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

@pedido_rota.delete("/pedido/{pedido_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_pedido(pedido_id: int, db: Session = Depends(database.get_db)):
    try:
        PedidoController.deletar_pedido(db, pedido_id)
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