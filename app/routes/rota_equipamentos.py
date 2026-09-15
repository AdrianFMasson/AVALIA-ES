from fastapi import APIRouter, Depends, status, HTTPException
from entities.models import Equipamentos, EquipamentoPublico
from sqlmodel import Session
from dependencies.dependencies import database
from controller import EquipamentosController

equipamentos_rota = APIRouter()


@equipamentos_rota.get("/equipamentos", status_code=status.HTTP_200_OK)
def buscar_equipamentos(db: Session = Depends(database.get_db)):
    try:
        equipamentos = EquipamentosController.buscar_equipamentos(db)
        return equipamentos
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=str(e)
        )


@equipamentos_rota.post("/equipamentos",
response_model= Equipamentos,
status_code=status.HTTP_201_CREATED)
def criar_equipamento(dados: Equipamentos,db:Session = Depends(database.get_db)):
    try:
        # Repassa a validação e a persistência para o controller
        return EquipamentosController.cadastrar_equipamento(db, dados)
    except ValueError as e:
         # Retorna HTTP 400 (Bad Request) se a categoria não existir ou houver conflito de dados
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=str(e)
        )
    except RuntimeError as e:
        # Retorna HTTP 500 (Internal Server Error) se o banco estiver inacessível
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=str(e)
        )
    
@equipamentos_rota.put("/equipamentos/{equipamento_id}", response_model=Equipamentos)
def atualizar_equipamento(equipamento_id: int, dados: EquipamentoPublico, db: Session = Depends(database.get_db)):
    try:
        return EquipamentosController.atualizar_equipamento(db, equipamento_id, dados)
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@equipamentos_rota.delete("/equipamentos/{equipamento_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_equipamento(equipamento_id: int, db: Session = Depends(database.get_db)):
    try:
        EquipamentosController.deletar_equipamento(db, equipamento_id)
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))