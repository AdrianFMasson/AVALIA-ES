from sqlmodel import SQLModel, Field
from datetime import datetime
from enum import Enum


class StatusPerfil(str, Enum):
    DISCENTE = "DISCENTE"
    GESTOR = "GESTOR"
    ADMINISTRADOR = "ADMINISTRADOR"

class Perfil(SQLModel,table=True):
    __tablename__="perfil"
    id_perfil:int | None = Field(default=None, primary_key=True)
    perfil: StatusPerfil = Field(default=StatusPerfil.DISCENTE)
    descricao_adicional: str = Field(max_length=100)

class Usuarios(SQLModel,table=True):
    __tablename__="usuarios"
    id_usuario: int | None = Field(default=None, primary_key=True)
    nome: str = Field(max_length=100)
    email: str = Field(max_length=100, unique=True)
    senha_hash: str =Field(max_length=255)
    id_perfil: int = Field(foreign_key="perfil.id_perfil")
    ativo: bool = Field(default=True)
    dt_cad_user: datetime = Field(default_factory=datetime.now)
    

class Estoque(SQLModel,table=True):
    __tablename__="estoque"
    id_estoque: int | None = Field(default=None,primary_key=True)
    descricao: str = Field(max_length=100)
    dt_cad_estoque: datetime = Field(default_factory=datetime.now)


class StatusEquip(str, Enum):
    DISPONIVEL = "DISPONIVEL"
    EMPRESTADO = "EMPRESTADO"
    MANUTENCAO = "MANUTENCAO"
    INATIVO = "INATIVO"


class Equipamentos(SQLModel,table=True):
    __tablename__="equipamentos"
    id_equipamento: int | None = Field(default=None,primary_key=True)
    id_estoque: int = Field(foreign_key="estoque.id_estoque")
    nome: str = Field(max_length=100)
    categoria: str = Field(max_length=100)
    descricao : str | None = Field(default=None)
    status_equip: StatusEquip = Field(default=StatusEquip.DISPONIVEL)
    dt_cad_equip: datetime = Field(default_factory=datetime.now)

class EquipamentoPublico(SQLModel):
    id_estoque: int
    nome: str = Field(max_length=100)
    categoria: str = Field(max_length=100)
    descricao: str | None = None
    status_equip: StatusEquip = StatusEquip.DISPONIVEL

class StatusPedido(str, Enum):
    ABERTO = "ABERTO"
    EM_ANALISE = "EM_ANALISE"
    ENCERRADO = "ENCERRADO"

class Pedido(SQLModel, table=True):
    __tablename__ = "pedido"
    id_pedido: int | None = Field(default=None, primary_key=True)
    status: StatusPedido = Field(default=StatusPedido.ABERTO)
    id_usuario: int = Field(foreign_key="usuarios.id_usuario")
    id_equipamento: int = Field(foreign_key="equipamentos.id_equipamento")
    data_pedido: datetime = Field(default_factory=datetime.now)

class StatusSolicitacao(str, Enum):
    SOLICITADO = "SOLICITADO"
    APROVADO = "APROVADO"
    NEGADO = "NEGADO"

class Emprestimos(SQLModel, table=True):
    __tablename__ = "emprestimos"
    id_emprestimo: int | None = Field(default=None, primary_key=True)
    id_gestor: int = Field(foreign_key="usuarios.id_usuario")
    id_pedido: int = Field(foreign_key="pedido.id_pedido", unique=True)
    data_aprovacao: datetime | None = None
    data_retirada: datetime | None = None
    data_prevista_devolucao: datetime | None = None
    data_devolucao: datetime | None = None
    status_solicitacao: StatusSolicitacao = Field(
        default=StatusSolicitacao.SOLICITADO
    )