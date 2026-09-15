from fastapi import APIRouter, Depends, status, HTTPException
from entities.models import Emprestimos
from sqlmodel import Session
from dependencies.dependencies import database
from controller import EmprestimosController

emprestimos_rota = APIRouter()

@emprestimos_rota.get("/emprestimos", status_code=status.HTTP_200_OK)
def buscar_emprestimos(db: Session = Depends(database.get_db)):
    try:
        emprestimos = EmprestimosController.buscar_emprestimos(db)
        return emprestimos
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@emprestimos_rota.post("/emprestimos",
    response_model=Emprestimos,
    status_code=status.HTTP_201_CREATED)
def criar_emprestimo(dados: Emprestimos, db: Session = Depends(database.get_db)):
    try:
        return EmprestimosController.cadastrar_emprestimo(db, dados)
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

@emprestimos_rota.put("/emprestimos/{emprestimo_id}", response_model=Emprestimos)
def atualizar_emprestimo(emprestimo_id: int, dados: Emprestimos, db: Session = Depends(database.get_db)):
    try:
        return EmprestimosController.atualizar_emprestimo(db, emprestimo_id, dados)
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

@emprestimos_rota.delete("/emprestimos/{emprestimo_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_emprestimo(emprestimo_id: int, db: Session = Depends(database.get_db)):
    try:
        EmprestimosController.deletar_emprestimo(db, emprestimo_id)
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