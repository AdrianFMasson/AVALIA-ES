import re


def validar_senha(senha: str) -> tuple[bool, str]:
    if len(senha) < 6:
        return False, "A senha deve possuir pelo menos 6 caracteres."

    if not re.search(r"[A-Z]", senha):
        return False, "A senha deve conter pelo menos uma letra maiúscula."

    if not re.search(r"[a-z]", senha):
        return False, "A senha deve conter pelo menos uma letra minúscula."

    if not re.search(r"[^A-Za-z0-9]", senha):
        return False, "A senha deve conter pelo menos um caractere especial."

    return True, "Senha válida."