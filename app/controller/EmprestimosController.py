from typing import List
from datetime import datetime

from sqlmodel import Session, select
from sqlalchemy.exc import OperationalError, IntegrityError

from entities.models import (
    Emprestimos,
    Usuarios,
    Pedido,
    StatusSolicitacao
)


def buscar_emprestimos(db: Session) -> List[Emprestimos]:
    try:
        statement = select(Emprestimos)
        emprestimos = db.exec(statement).all()
        return emprestimos

    except OperationalError as e:
        raise RuntimeError(
            "Falha de comunicação com o banco de dados."
        ) from e


def cadastrar_emprestimo(
    db: Session,
    dados: Emprestimos
) -> Emprestimos:

    try:
        gestor = db.get(Usuarios, dados.id_gestor)

        if gestor is None:
            raise ValueError(
                "O gestor informado não está cadastrado no sistema."
            )

        pedido = db.get(Pedido, dados.id_pedido)

        if pedido is None:
            raise ValueError(
                "O pedido informado não está cadastrado no sistema."
            )

        novo_emprestimo = Emprestimos(
            id_gestor=dados.id_gestor,
            id_pedido=dados.id_pedido,
            data_aprovacao=dados.data_aprovacao,
            data_retirada=dados.data_retirada,
            data_prevista_devolucao=dados.data_prevista_devolucao,
            data_devolucao=dados.data_devolucao,
            status_solicitacao=dados.status_solicitacao
        )

        db.add(novo_emprestimo)
        db.commit()
        db.refresh(novo_emprestimo)

        return novo_emprestimo

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


def atualizar_emprestimo(
    db: Session,
    emprestimo_id: int,
    dados: Emprestimos
) -> Emprestimos:

    try:
        emprestimo = db.get(Emprestimos, emprestimo_id)

        if emprestimo is None:
            raise KeyError(
                f"Empréstimo de ID {emprestimo_id} não encontrado."
            )

        gestor = db.get(Usuarios, dados.id_gestor)

        if gestor is None:
            raise ValueError(
                "O gestor informado não está cadastrado no sistema."
            )

        pedido = db.get(Pedido, dados.id_pedido)

        if pedido is None:
            raise ValueError(
                "O pedido informado não está cadastrado no sistema."
            )

        emprestimo.id_gestor = dados.id_gestor
        emprestimo.id_pedido = dados.id_pedido
        emprestimo.status_solicitacao = dados.status_solicitacao

        if dados.status_solicitacao == StatusSolicitacao.APROVADO:
            emprestimo.data_aprovacao = datetime.now()

        elif dados.status_solicitacao == StatusSolicitacao.NEGADO:
            emprestimo.data_aprovacao = None

        else:
            emprestimo.data_aprovacao = dados.data_aprovacao

        if dados.data_retirada is not None:
            emprestimo.data_retirada = dados.data_retirada

        if dados.data_prevista_devolucao is not None:
            emprestimo.data_prevista_devolucao = (
                dados.data_prevista_devolucao
            )

        if dados.data_devolucao is not None:
            emprestimo.data_devolucao = dados.data_devolucao

        db.add(emprestimo)
        db.commit()
        db.refresh(emprestimo)

        return emprestimo

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


def deletar_emprestimo(
    db: Session,
    emprestimo_id: int
):
    try:
        emprestimo = db.get(Emprestimos, emprestimo_id)

        if emprestimo is None:
            raise KeyError(
                f"Empréstimo de ID {emprestimo_id} não encontrado."
            )

        db.delete(emprestimo)
        db.commit()

    except IntegrityError as e:
        db.rollback()

        raise ValueError(
            "Não foi possível excluir o empréstimo."
        ) from e

    except OperationalError as e:
        db.rollback()

        raise RuntimeError(
            "Falha de comunicação com o banco de dados."
        ) from e