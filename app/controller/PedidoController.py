from typing import List
from sqlmodel import Session, select
from sqlalchemy.exc import OperationalError, IntegrityError
from entities.models import Pedido, Usuarios, Equipamentos

def buscar_pedidos(db: Session) -> List[Pedido]:
    try:
        statement = select(Pedido)
        pedidos = db.exec(statement).all()
        return pedidos
    except OperationalError as e:
        raise RuntimeError(
            "Falha de comunicação com o banco de dados."
        ) from e

def cadastrar_pedido(db: Session, dados: Pedido) -> Pedido:
    try:
        usuario = db.get(Usuarios, dados.id_usuario)
        if usuario is None:
            raise ValueError(
                "O usuário informado não está cadastrado no sistema."
            )
        equipamento = db.get(Equipamentos, dados.id_equipamento)
        if equipamento is None:
            raise ValueError(
                "O equipamento informado não está cadastrado no sistema."
            )
        novo_pedido = Pedido(
            **dados.model_dump()
        )
        db.add(novo_pedido)
        db.commit()
        db.refresh(novo_pedido)
        return novo_pedido
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

def atualizar_pedido(db: Session, pedido_id: int, dados: Pedido) -> Pedido:
    try:
        pedido = db.get(Pedido, pedido_id)
        if pedido is None:
            raise KeyError(
                f"Pedido de ID {pedido_id} não encontrado."
            )
        usuario = db.get(Usuarios, dados.id_usuario)
        if usuario is None:
            raise ValueError(
                "O usuário informado não está cadastrado no sistema."
            )
        equipamento = db.get(Equipamentos, dados.id_equipamento)
        if equipamento is None:
            raise ValueError(
                "O equipamento informado não está cadastrado no sistema."
            )
        pedido.status = dados.status
        pedido.id_usuario = dados.id_usuario
        pedido.id_equipamento = dados.id_equipamento
        db.add(pedido)
        db.commit()
        db.refresh(pedido)
        return pedido
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

def deletar_pedido(db: Session, pedido_id: int):
    try:
        pedido = db.get(Pedido, pedido_id)
        if pedido is None:
            raise KeyError(
                f"Pedido de ID {pedido_id} não encontrado."
            )
        db.delete(pedido)
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise ValueError(
            "Não foi possível excluir o pedido."
        ) from e
    except OperationalError as e:
        db.rollback()
        raise RuntimeError(
            "Falha de comunicação com o banco de dados."
        ) from e