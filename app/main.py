from fastapi import FastAPI, Depends, HTTPException, status
# from routes import rota_aluno, rota_item_cardapio
from sqlmodel import Session, select, SQLModel, Field
from config.Config import settings
from dependencies.dependencies import database
from routes.rota_estoque import estoque_rota
from routes.rota_equipamentos import equipamentos_rota
from routes.rota_perfil import perfil_rota
from routes.rota_usuarios import usuarios_rota
from routes.rota_pedido import pedido_rota
from routes.rota_emprestimos import emprestimos_rota

app = FastAPI(
    title="Minha API",
    description="API de exemplo com FastAPI",
    version="1.0.0"
)

app.include_router(estoque_rota)
app.include_router(equipamentos_rota)
app.include_router(perfil_rota)
app.include_router(usuarios_rota)
app.include_router(pedido_rota)
app.include_router(emprestimos_rota)


@app.get("/")
def root(s: Session = Depends(database.get_db)):
    return {"mensagem": "Olá, FastAPI!"}


# app.include_router(rota_aluno.aluno_rotas)
# app.include_router(rota_item_cardapio.item_cardapio_routes)


@app.get("/config")
def config():
    return settings