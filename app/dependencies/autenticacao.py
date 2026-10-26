from datetime import datetime, timedelta, timezone
import secrets

import jwt
from jwt import InvalidTokenError
from fastapi import HTTPException, Request, status
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, select

from config.Config import settings
from entities.models import Usuarios, Perfil
from entities.sessoes import Sessoes


def gerar_token_acesso(id_usuario: int, id_sessao: str) -> str:
    agora = datetime.now(timezone.utc)
    expiracao = agora + timedelta(
        minutes=settings.JWT_ACCESS_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(id_usuario),
        "sid": id_sessao,
        "iss": settings.JWT_ISSUER,
        "iat": agora,
        "exp": expiracao,
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def gerar_id_sessao() -> str:
    return secrets.token_urlsafe(32)


def validar_token_acesso(token: str) -> dict:
    payload = jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
        issuer=settings.JWT_ISSUER,
        options={
            "require": ["sub", "sid", "iss", "iat", "exp"],
            "verify_iat": True,
            "verify_exp": True,
            "verify_iss": True,
        },
    )

    agora = datetime.now(timezone.utc).timestamp()
    emitido_em = payload["iat"]
    expira_em = payload["exp"]

    if not isinstance(emitido_em, (int, float)):
        raise InvalidTokenError("Campo iat inválido.")

    if not isinstance(expira_em, (int, float)):
        raise InvalidTokenError("Campo exp inválido.")

    if emitido_em > agora:
        raise InvalidTokenError("Token emitido no futuro.")

    if expira_em <= emitido_em:
        raise InvalidTokenError("Expiração do token inválida.")

    if not isinstance(payload["sub"], str) or not payload["sub"]:
        raise InvalidTokenError("Campo sub inválido.")

    if not isinstance(payload["sid"], str) or not payload["sid"]:
        raise InvalidTokenError("Campo sid inválido.")

    return payload


def criar_sessao(
    db: Session,
    id_usuario: int,
) -> tuple[Sessoes, str]:
    agora = datetime.now(timezone.utc)
    expiracao = agora + timedelta(
        minutes=settings.JWT_ACCESS_EXPIRE_MINUTES
    )

    try:
        sessoes_anteriores = db.exec(
            select(Sessoes).where(
                Sessoes.id_usuario == id_usuario,
                Sessoes.ativa.is_(True),
            )
        ).all()

        for sessao in sessoes_anteriores:
            sessao.ativa = False
            db.add(sessao)

        id_sessao = gerar_id_sessao()

        nova_sessao = Sessoes(
            id_sessao=id_sessao,
            id_usuario=id_usuario,
            dt_criacao=agora.replace(tzinfo=None),
            dt_expiracao=expiracao.replace(tzinfo=None),
            ativa=True,
        )

        db.add(nova_sessao)
        db.commit()
        db.refresh(nova_sessao)

        token = gerar_token_acesso(id_usuario, id_sessao)

        return nova_sessao, token

    except SQLAlchemyError:
        db.rollback()
        raise


def obter_sessao_ativa(
    db: Session,
    id_sessao: str,
    id_usuario: int,
) -> Sessoes | None:
    try:
        sessao = db.get(Sessoes, id_sessao)

        if sessao is None or not sessao.ativa:
            return None

        if sessao.id_usuario != id_usuario:
            return None

        agora = datetime.now(timezone.utc).replace(tzinfo=None)

        if sessao.dt_expiracao <= agora:
            sessao.ativa = False
            db.add(sessao)
            db.commit()
            return None

        return sessao

    except SQLAlchemyError:
        db.rollback()
        raise


def encerrar_sessao(
    db: Session,
    id_sessao: str,
) -> bool:
    try:
        sessao = db.get(Sessoes, id_sessao)

        if sessao is None or not sessao.ativa:
            return False

        sessao.ativa = False
        db.add(sessao)
        db.commit()

        return True

    except SQLAlchemyError:
        db.rollback()
        raise


def encerrar_sessao_por_token(
    db: Session,
    token: str,
) -> bool:
    if not token:
        return False

    try:
        payload = validar_token_acesso(token)
        id_sessao = payload["sid"]
        id_usuario = int(payload["sub"])

        return encerrar_sessao_se_usuario_corresponder(
            db,
            id_sessao,
            id_usuario,
        )

    except (InvalidTokenError, ValueError, TypeError, KeyError):
        return False


def encerrar_sessao_se_usuario_corresponder(
    db: Session,
    id_sessao: str,
    id_usuario: int,
) -> bool:
    try:
        sessao = db.get(Sessoes, id_sessao)

        if (
            sessao is None
            or sessao.id_usuario != id_usuario
            or not sessao.ativa
        ):
            return False

        sessao.ativa = False
        db.add(sessao)
        db.commit()

        return True

    except SQLAlchemyError:
        db.rollback()
        raise


def obter_usuario_autenticado(
    request: Request,
    db: Session,
) -> dict | None:
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
        sessao = obter_sessao_ativa(
            db,
            id_sessao,
            id_usuario,
        )

        if sessao is None:
            return None

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
            "perfil": perfil.perfil.value,
        }

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível validar a autenticação. Tente novamente.",
        )