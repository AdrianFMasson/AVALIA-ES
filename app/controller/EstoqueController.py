from entities.models import Estoque
from sqlmodel import Session


def inserir_estoque(categoria:Estoque,db:Session):
    categoria_insert = Estoque.model_validate(categoria)
    db.add(categoria_insert)
    db.commit()
    db.refresh(categoria_insert)
    return categoria_insert