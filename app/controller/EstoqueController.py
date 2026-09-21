from typing import List

from datetime import datetime

from sqlmodel import Session, select

from sqlalchemy.exc import OperationalError, IntegrityError

from entities.models import Estoque


def buscar_estoques(db: Session) -> List[Estoque]:
    try:
        statement = select(Estoque)

        estoques = db.exec(statement).all()

        return estoques

    except OperationalError as e:
        raise RuntimeError(
            "Falha de comunicação com o banco de dados."
        ) from e


def cadastrar_estoque(
    db: Session,
    dados: Estoque
) -> Estoque:

    try:
        novo_estoque = Estoque(
            descricao=dados.descricao,
            dt_cad_estoque=dados.dt_cad_estoque
        )

        db.add(novo_estoque)

        db.commit()

        db.refresh(novo_estoque)

        return novo_estoque

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


def atualizar_estoque(
    db: Session,
    estoque_id: int,
    dados: Estoque
) -> Estoque:

    try:
        estoque = db.get(Estoque, estoque_id)

        if estoque is None:
            raise KeyError(
                f"Estoque de ID {estoque_id} não encontrado."
            )

        estoque.descricao = dados.descricao

        if dados.dt_cad_estoque is not None:
            estoque.dt_cad_estoque = dados.dt_cad_estoque

        db.add(estoque)

        db.commit()

        db.refresh(estoque)

        return estoque

    except IntegrityError as e:
        db.rollback()

        raise ValueError(
            "Erro de integridade nos dados informados."
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


def deletar_estoque(
    db: Session,
    estoque_id: int
):
    try:
        estoque = db.get(Estoque, estoque_id)

        if estoque is None:
            raise KeyError(
                f"Estoque de ID {estoque_id} não encontrado."
            )

        db.delete(estoque)

        db.commit()

    except IntegrityError as e:
        db.rollback()

        raise ValueError(
            "Não foi possível excluir o estoque. "
            "Verifique se existem equipamentos vinculados a ele."
        ) from e

    except OperationalError as e:
        db.rollback()

        raise RuntimeError(
            "Falha de comunicação com o banco de dados."
        ) from e