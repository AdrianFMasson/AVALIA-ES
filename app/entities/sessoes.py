from datetime import datetime
from sqlmodel import SQLModel, Field


class Sessoes(SQLModel, table=True):
    __tablename__ = "sessoes"

    id_sessao: str = Field(primary_key=True, max_length=100)
    id_usuario: int = Field(
        foreign_key="usuarios.id_usuario",
        index=True
    )
    dt_criacao: datetime = Field(default_factory=datetime.now)
    dt_expiracao: datetime
    ativa: bool = Field(default=True)