from typing import List
from datetime import datetime
from sqlmodel import Session, select
from sqlalchemy.exc import OperationalError, IntegrityError
from entities.models import UsuarioLogin,UsuarioLogado,Usuarios,Perfil
from core.secutity import verifica_senha,create_token

def fazer_login(db:Session,username:str,password:str):
    try:
        usuario=db.exec(select(Usuarios).where(Usuarios.email==username)).first()
        usuario= usuario is not None and verifica_senha(password,usuario.senha)
        if not usuario:
            raise ValueError("Credenciais Inválidas")
        roles=db.exec(select(Perfil.perfil).join(Usuarios).
                      where(Usuarios.id_perfil == usuario.id_perfil)).all()
        token=create_token(str(usuario.id_usuario),roles)
        return{"token_type":"bearer","acess_token":token}
    except OperationalError as e:
        raise ValueError("Credenciais Inválidas")