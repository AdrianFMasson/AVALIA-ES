from typing import List
from sqlmodel import Session, select
from sqlalchemy.exc import OperationalError, IntegrityError
from entities.models import Emprestimos, Usuarios, Pedido

def buscar_emprestimos(db: Session) -> List[Emprestimos]:
    try:
        statement = select(Emprestimos)
        emprestimos = db.exec(statement).all()
        return emprestimos
    except OperationalError as e:
        raise RuntimeError(
            "Falha de comunicação com o banco de dados."
        ) from e

def cadastrar_emprestimo(db: Session, dados: Emprestimos) -> Emprestimos:
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
            **dados.model_dump()
        )
        db.add(novo_emprestimo)
        db.commit()
        db.refresh(novo_emprestimo)
        return novo_emprestimo
    except IntegrityError as e:
        db.rollback()
        raise ValueError(
            "Erro nos dados informados. Verifique e tente novamente."
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
        emprestimo.data_aprovacao = dados.data_aprovacao
        emprestimo.data_retirada = dados.data_retirada
        emprestimo.data_prevista_devolucao = dados.data_prevista_devolucao
        emprestimo.data_devolucao = dados.data_devolucao
        emprestimo.status_solicitacao = dados.status_solicitacao
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
        raise RuntimeError(
            "Falha de comunicação com o banco de dados."
        ) from e

def deletar_emprestimo(db: Session, emprestimo_id: int):
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