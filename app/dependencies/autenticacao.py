from fastapi import Request, HTTPException, status
from jwt import InvalidTokenError
from sqlmodel import Session
from sqlalchemy.exc import SQLAlchemyError

from entities.models import Usuarios, Perfil
from utils.autenticacao import validar_token_acesso, obter_sessao_ativa


def obter_usuario_autenticado(request: Request, db: Session):
    token = request.cookies.get("access_token")

    if not token:
        return None

    try:
        payload = validar_token_acesso(token)
        id_usuario = int(payload["sub"])
        id_sessao = payload["sid"]
    except (InvalidTokenError, ValueError, KeyError, TypeError):
        return None

    try:
        sessao = obter_sessao_ativa(db, id_sessao, id_usuario)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível validar a sessão. Tente novamente."
        )

    if sessao is None:
        return None

    try:
        usuario = db.get(Usuarios, id_usuario)

        if usuario is None or not usuario.ativo:
            sessao.ativa = False
            db.add(sessao)
            db.commit()
            return None

        perfil = db.get(Perfil, usuario.id_perfil)

        if perfil is None:
            return None

        return {
            "usuario": usuario,
            "perfil": perfil.perfil.value
        }

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível validar o usuário. Tente novamente."
        )