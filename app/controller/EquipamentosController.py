from typing import List

from sqlmodel import Session, select
from sqlalchemy.exc import OperationalError, IntegrityError

from entities.models import Equipamentos, EquipamentoPublico, Estoque


def buscar_equipamentos(db: Session) -> List[Equipamentos]:
    try:
        statement = select(Equipamentos)
        equipamentos = db.exec(statement).all()
        return equipamentos

    except OperationalError as e:
        raise RuntimeError(
            "Falha de comunicação com o banco de dados."
        ) from e


def cadastrar_equipamento(
    db: Session,
    dados_entrada: EquipamentoPublico
) -> Equipamentos:
    try:
        # Verifica se o estoque informado existe.
        if dados_entrada.id_estoque is not None:
            estoque = db.get(
Estoque,dados_entrada.id_estoque)

            if estoque is None:
                raise ValueError("O estoque informado não está cadastrado no sistema.")
        # Cria o equipamento.
        novo_equipamento = Equipamentos(**dados_entrada.model_dump())

        # Salva no banco.
        db.add(novo_equipamento)
        db.commit()
        db.refresh(novo_equipamento)
        return novo_equipamento

    except IntegrityError as e:
        db.rollback()
        raise ValueError("Erro nos dados informados. ""Verifique e tente novamente.") from e

    except OperationalError as e:
        db.rollback()
        print("ERRO DO BANCO:")
        print(e)
        print("CAUSA ORIGINAL:")
        print(e.orig)

        raise RuntimeError(f"Erro do banco de dados: {e.orig}") from e


def atualizar_equipamento(
    db: Session,
    equipamento_id: int,
    dados: EquipamentoPublico
) -> Equipamentos:
    try:
        # Procura o equipamento
        equipamento = db.get(
            Equipamentos,
            equipamento_id
        )

        if equipamento is None:
            raise KeyError(
                f"Equipamento de ID {equipamento_id} não encontrado."
            )

        # Verifica se o estoque informado existe
        estoque = db.get(
            Estoque,
            dados.id_estoque
        )

        if estoque is None:
            raise ValueError(
                "O estoque informado não está cadastrado no sistema."
            )

        # Atualiza os dados
        equipamento.id_estoque = dados.id_estoque
        equipamento.nome = dados.nome
        equipamento.categoria = dados.categoria
        equipamento.descricao = dados.descricao
        equipamento.status_equip = dados.status_equip

        # Salva as alterações
        db.add(equipamento)
        db.commit()
        db.refresh(equipamento)

        return equipamento

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

def deletar_equipamento(db: Session,equipamento_id: int):
    try:
        # Procura o equipamento.
        equipamento = db.get(Equipamentos,equipamento_id)

        if equipamento is None:
            raise KeyError(f"Equipamento de ID {equipamento_id} não encontrado.")
        # Exclui o equipamento.
        db.delete(equipamento)
        db.commit()

    except IntegrityError as e:
        db.rollback()
        raise ValueError("Não foi possível excluir o equipamento.") from e

    except OperationalError as e:
        db.rollback()
        raise RuntimeError("Falha de comunicação com o banco de dados.") from e