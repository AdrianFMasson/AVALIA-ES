from fastapi import APIRouter, Depends
from  entities.models import Estoque
from sqlmodel import Session
from dependencies.dependencies import database
from controller.EstoqueController import inserir_estoque


estoque_rota = APIRouter()

@estoque_rota.post("/estoque")
def inserir(categoria:Estoque,db: Session = Depends(database.get_db)):
    inserir_estoque(categoria,db)