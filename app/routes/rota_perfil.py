from fastapi import APIRouter, Depends, status, HTTPException
from entities.models import Perfil
from sqlmodel import Session
from dependencies.dependencies import database
from controller import PerfilController

perfil_rota = APIRouter()

@perfil_rota.get("/perfil", status_code=status.HTTP_200_OK)
def buscar_perfis(db: Session = Depends(database.get_db)):
    try:
        perfis = PerfilController.buscar_perfis(db)
        return perfis
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@perfil_rota.post("/perfil",
    response_model=Perfil,
    status_code=status.HTTP_201_CREATED)
def criar_perfil(dados: Perfil, db: Session = Depends(database.get_db)):
    try:
        return PerfilController.cadastrar_perfil(db, dados)
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

@perfil_rota.put("/perfil/{perfil_id}", response_model=Perfil)
def atualizar_perfil(perfil_id: int, dados: Perfil, db: Session = Depends(database.get_db)):
    try:
        return PerfilController.atualizar_perfil(db, perfil_id, dados)
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

@perfil_rota.delete("/perfil/{perfil_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_perfil(perfil_id: int, db: Session = Depends(database.get_db)):
    try:
        PerfilController.deletar_perfil(db, perfil_id)
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