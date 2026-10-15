
from typing import List
from sqlmodel import Session, select
from sqlalchemy.exc import OperationalError, IntegrityError, SQLAlchemyError
from entities.models import Pedido, Usuarios, Equipamentos

def buscar_pedidos(db: Session) -> List[Pedido]:
    try:
        return db.exec(select(Pedido)).all()
    except SQLAlchemyError as e:
        db.rollback()
        print("ERRO AO BUSCAR PEDIDOS:", repr(e))
        raise RuntimeError("Falha ao consultar os pedidos no banco de dados.") from e

def cadastrar_pedido(db: Session, dados: Pedido) -> Pedido:
    try:
        usuario = db.get(Usuarios, dados.id_usuario)
        if usuario is None:
            raise ValueError("O usuário informado não está cadastrado no sistema.")
        equipamento = db.get(Equipamentos, dados.id_equipamento)
        if equipamento is None:
            raise ValueError("O equipamento informado não está cadastrado no sistema.")
        dados_pedido = dados.model_dump(exclude={"id_pedido"})
        novo_pedido = Pedido(**dados_pedido)
        db.add(novo_pedido)
        db.commit()
        db.refresh(novo_pedido)
        return novo_pedido
    except (ValueError, KeyError):
        db.rollback()
        raise
    except IntegrityError as e:
        db.rollback()
        print("ERRO DE INTEGRIDADE AO CADASTRAR PEDIDO:", repr(e))
        raise ValueError("Erro nos dados informados. Verifique e tente novamente.") from e
    except SQLAlchemyError as e:
        db.rollback()
        print("ERRO AO CADASTRAR PEDIDO:", repr(e))
        raise RuntimeError("Falha ao cadastrar o pedido no banco de dados.") from e

def atualizar_pedido(db: Session, pedido_id: int, dados: Pedido) -> Pedido:
    try:
        pedido = db.get(Pedido, pedido_id)
        if pedido is None:
            raise KeyError(f"Pedido de ID {pedido_id} não encontrado.")
        usuario = db.get(Usuarios, dados.id_usuario)
        if usuario is None:
            raise ValueError("O usuário informado não está cadastrado no sistema.")
        equipamento = db.get(Equipamentos, dados.id_equipamento)
        if equipamento is None:
            raise ValueError("O equipamento informado não está cadastrado no sistema.")
        pedido.status = dados.status
        pedido.id_usuario = dados.id_usuario
        pedido.id_equipamento = dados.id_equipamento
        db.add(pedido)
        db.commit()
        db.refresh(pedido)
        return pedido
    except (ValueError, KeyError):
        db.rollback()
        raise
    except IntegrityError as e:
        db.rollback()
        print("ERRO DE INTEGRIDADE AO ATUALIZAR PEDIDO:", repr(e))
        raise ValueError("Erro de integridade nos dados informados.") from e
    except SQLAlchemyError as e:
        db.rollback()
        print("ERRO AO ATUALIZAR PEDIDO:", repr(e))
        raise RuntimeError(f"Falha ao atualizar o pedido: {e}") from e

def deletar_pedido(db: Session, pedido_id: int):
    try:
        pedido = db.get(Pedido, pedido_id)
        if pedido is None:
            raise KeyError(f"Pedido de ID {pedido_id} não encontrado.")
        db.delete(pedido)
        db.commit()
    except KeyError:
        db.rollback()
        raise
    except IntegrityError as e:
        db.rollback()
        print("ERRO DE INTEGRIDADE AO EXCLUIR PEDIDO:", repr(e))
        raise ValueError("Não foi possível excluir o pedido.") from e
    except SQLAlchemyError as e:
        db.rollback()
        print("ERRO AO EXCLUIR PEDIDO:", repr(e))
        raise RuntimeError("Falha ao excluir o pedido no banco de dados.") from e
