from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError

_hasher = PasswordHash.recommended()

def gerar_hash_senha(senha: str) -> str:
    return _hasher.hash(senha)

def verificar_senha(senha: str, senha_hash: str) -> bool:
    if not senha or not senha_hash:
        return False
    try:
        return _hasher.verify(senha, senha_hash)
    except (UnknownHashError, ValueError, TypeError):
        return False