from datetime import datetime, timedelta, timezone
import jwt
from passlib.context import CryptContext
from config.Config import Settings



pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def criptografar_senha(senha:str):
    return pwd_context.hash(senha)


def verifica_senha(senha_plana:str,senha_banco:str):
    return pwd_context.verify(senha_plana,senha_banco)


def create_token(id_usuario:str,roles:list[str]):
    vence_em=datetime.now(timezone.utc)+Settings.JWT_ACCESS_EXPIRE_MINUTES
    payload={
        "sub":id_usuario,
        "exp":vence_em,
        "roles":roles,
        "iss":Settings.JWT_ISSUER
    }
    token=jwt.encode(payload,
                     Settings.JWT_SECRET_KEY,
                     Settings.JWT_ALGORITHM)
    return token