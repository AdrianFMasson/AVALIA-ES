from typing import List
from sqlmodel import Session, select
from sqlalchemy.exc import OperationalError, IntegrityError
from entities.models import Usuarios, Perfil


def buscar_usuarios(db: Session) -> List[Usuarios]:
    try:
        statement = select(Usuarios)
        usuarios = db.exec(statement).all()
        return usuarios
    except OperationalError as e:
        raise RuntimeError(
            "Falha de comunicação com o banco de dados."
        ) from e


def cadastrar_usuario(db: Session, dados: Usuarios) -> Usuarios:
    try:
        # Verifica se o perfil informado existe.
        perfil = db.get(Perfil, dados.id_perfil)

        if perfil is None:
            raise ValueError(
                "O perfil informado não está cadastrado no sistema."
            )

        # Cria o usuário.
        novo_usuario = Usuarios(
            **dados.model_dump()
        )

        # Salva no banco.
        db.add(novo_usuario)
        db.commit()
        db.refresh(novo_usuario)

        return novo_usuario

    except IntegrityError as e:
        db.rollback()
        raise ValueError(
            "Erro nos dados informados. "
            "Verifique e tente novamente."
        ) from e

    except OperationalError as e:
        db.rollback()
        print("ERRO DO BANCO:")
        print(e)
        print("CAUSA ORIGINAL:")
        print(e.orig)
        raise RuntimeError(
            f"Erro do banco de dados: {e.orig}"
        ) from e


def atualizar_usuario(
    db: Session,
    usuario_id: int,
    dados: Usuarios
) -> Usuarios:
    try:
        # Procura o usuário.
        usuario = db.get(Usuarios, usuario_id)

        if usuario is None:
            raise KeyError(
                f"Usuário de ID {usuario_id} não encontrado."
            )

        # Verifica se o perfil informado existe.
        perfil = db.get(Perfil, dados.id_perfil)

        if perfil is None:
            raise ValueError(
                "O perfil informado não está cadastrado no sistema."
            )

        # Atualiza os dados.
        usuario.nome = dados.nome
        usuario.email = dados.email
        usuario.senha_hash = dados.senha_hash
        usuario.id_perfil = dados.id_perfil
        usuario.ativo = dados.ativo

        # Salva as alterações.
        db.add(usuario)
        db.commit()
        db.refresh(usuario)

        return usuario

    except IntegrityError as e:
        db.rollback()
        raise ValueError(
            "Erro de integridade nos dados informados."
        ) from e

    except OperationalError as e:
        db.rollback()
        raise RuntimeError(
            "Falha de comunicação com o banco de dados."
        ) from e


def deletar_usuario(db: Session, usuario_id: int):
    try:
        # Procura o usuário.
        usuario = db.get(Usuarios, usuario_id)

        if usuario is None:
            raise KeyError(
                f"Usuário de ID {usuario_id} não encontrado."
            )

        # Exclui o usuário.
        db.delete(usuario)
        db.commit()

    except IntegrityError as e:
        db.rollback()
        raise ValueError(
            "Não foi possível excluir o usuário."
        ) from e

    except OperationalError as e:
        db.rollback()
        raise RuntimeError(
            "Falha de comunicação com o banco de dados."
        ) from e