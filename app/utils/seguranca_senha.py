from pwdlib import PasswordHash

_hasher = PasswordHash.recommended()


def gerar_hash_senha(senha: str) -> str:
    return _hasher.hash(senha)


def verificar_senha(senha: str, senha_hash: str) -> bool:
    try:
        return _hasher.verify(senha, senha_hash)
    except (ValueError, TypeError):
        return False