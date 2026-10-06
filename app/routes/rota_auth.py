from fastapi import APIRouter, Depends, status, HTTPException
from entities.models import UsuarioLogin
from sqlmodel import Session
from dependencies.dependencies import database
from controller import AuthController
auth_rota =  APIRouter()

@auth_rota.post("/auth/login")
def usuario_login(credenciais:UsuarioLogin,
                  db:Session=Depends(database.get_db),):
    try:
        token=AuthController.fazer_login(db,credenciais.usuario,credenciais.senha)
        return token
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail=str(e))
    