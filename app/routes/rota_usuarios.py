from fastapi import APIRouter, Depends, status, HTTPException
from entities.models import Usuarios
from sqlmodel import Session
from dependencies.dependencies import database
from controller import UsuariosController

usuarios_rota = APIRouter()

@usuarios_rota.get("/usuarios", status_code=status.HTTP_200_OK)
def buscar_usuarios(db: Session = Depends(database.get_db)):
    try:
        usuarios = UsuariosController.buscar_usuarios(db)
        return usuarios
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@usuarios_rota.post("/usuarios",
    response_model=Usuarios,
    status_code=status.HTTP_201_CREATED)
def criar_usuario(dados: Usuarios, db: Session = Depends(database.get_db)):
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

@usuarios_rota.put("/usuarios/{usuario_id}", response_model=Usuarios)
def atualizar_usuario(usuario_id: int, dados: Usuarios, db: Session = Depends(database.get_db)):
    try:
        return UsuariosController.atualizar_usuario(db, usuario_id, dados)
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

@usuarios_rota.delete("/usuarios/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_usuario(usuario_id: int, db: Session = Depends(database.get_db)):
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