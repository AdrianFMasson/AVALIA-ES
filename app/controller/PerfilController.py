from typing import List

from sqlmodel import Session, select

from sqlalchemy.exc import OperationalError, IntegrityError

from entities.models import Perfil


def buscar_perfis(db: Session) -> List[Perfil]:

    try:
        statement = select(Perfil)
        perfis = db.exec(statement).all()

        return perfis

    except OperationalError as e:
        raise RuntimeError(
            "Falha de comunicação com o banco de dados."
        ) from e


def cadastrar_perfil(
    db: Session,
    dados: Perfil
) -> Perfil:

    try:
        # Cria o perfil.
        novo_perfil = Perfil(
            **dados.model_dump()
        )

        # Salva no banco.
        db.add(novo_perfil)
        db.commit()
        db.refresh(novo_perfil)

        return novo_perfil

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


def atualizar_perfil(
    db: Session,
    perfil_id: int,
    dados: Perfil
) -> Perfil:

    try:
        # Procura o perfil.
        perfil = db.get(
            Perfil,
            perfil_id
        )

        if perfil is None:
            raise KeyError(
                f"Perfil de ID {perfil_id} não encontrado."
            )

        # Atualiza os dados.
        perfil.perfil = dados.perfil
        perfil.descricao_adicional = dados.descricao_adicional

        # Salva as alterações.
        db.add(perfil)
        db.commit()
        db.refresh(perfil)

        return perfil

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


def deletar_perfil(
    db: Session,
    perfil_id: int
):

    try:
        # Procura o perfil.
        perfil = db.get(
            Perfil,
            perfil_id
        )

        if perfil is None:
            raise KeyError(
                f"Perfil de ID {perfil_id} não encontrado."
            )

        # Exclui o perfil.
        db.delete(perfil)
        db.commit()

    except IntegrityError as e:
        db.rollback()

        raise ValueError(
            "Não foi possível excluir o perfil."
        ) from e

    except OperationalError as e:
        db.rollback()

        raise RuntimeError(
            "Falha de comunicação com o banco de dados."
        ) from e