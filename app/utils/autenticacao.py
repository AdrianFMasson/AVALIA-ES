from datetime import datetime, timedelta, timezone
import secrets
import jwt
from sqlalchemy.exc import OperationalError
from sqlmodel import Session, select
from config.Config import settings
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
        "exp": expiracao
    }
    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )


def gerar_id_sessao() -> str:
    return secrets.token_urlsafe(32)


def validar_token_acesso(token: str) -> dict:
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
        issuer=settings.JWT_ISSUER,
        options={"require": ["sub", "sid", "iss", "iat", "exp"]}
    )


def criar_sessao(db: Session, id_usuario: int) -> tuple[Sessoes, str]:
    agora = datetime.now(timezone.utc)
    expiracao = agora + timedelta(
        minutes=settings.JWT_ACCESS_EXPIRE_MINUTES
    )

    try:
        # Invalida todas as sessões anteriores desse usuário.
        sessoes_anteriores = db.exec(
            select(Sessoes).where(
                Sessoes.id_usuario == id_usuario,
                Sessoes.ativa == True
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
            ativa=True
        )

        db.add(nova_sessao)
        db.commit()
        db.refresh(nova_sessao)

        token = gerar_token_acesso(id_usuario, id_sessao)
        return nova_sessao, token

    except OperationalError:
        db.rollback()
        raise


def obter_sessao_ativa(db: Session, id_sessao: str, id_usuario: int):
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


def encerrar_sessao(db: Session, id_sessao: str) -> bool:
    sessao = db.get(Sessoes, id_sessao)

    if sessao is None or not sessao.ativa:
        return False

    sessao.ativa = False
    db.add(sessao)
    db.commit()
    return True