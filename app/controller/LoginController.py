from sqlmodel import Session, select
from sqlalchemy.exc import OperationalError
from entities.models import Usuarios, Perfil
from utils.seguranca_senha import verificar_senha


def autenticar_usuario(db: Session, email: str, senha: str):
    try:
        statement = select(Usuarios).where(Usuarios.email == email)
        usuario = db.exec(statement).first()

        if usuario is None:
            raise ValueError("E-mail ou senha inválidos.")

        if not usuario.ativo:
            raise ValueError("Esta conta está desativada.")

        if not verificar_senha(senha, usuario.senha_hash):
            raise ValueError("E-mail ou senha inválidos.")

        perfil = db.get(Perfil, usuario.id_perfil)

        if perfil is None:
            raise ValueError("O perfil deste usuário não está cadastrado.")

        return {
            "id_usuario": usuario.id_usuario,
            "nome": usuario.nome,
            "email": usuario.email,
            "perfil": perfil.perfil.value
        }

    except OperationalError as e:
        raise RuntimeError(
            "Falha de comunicação com o banco de dados."
        ) from e