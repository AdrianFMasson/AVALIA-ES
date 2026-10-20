from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlmodel import Session
from sqlalchemy.exc import SQLAlchemyError

from dependencies.dependencies import database

from routes import (
    rota_estoque,
    rota_equipamentos,
    rota_perfil,
    rota_usuarios,
    rota_pedido,
    rota_emprestimos,
    rota_login,
    rota_discente,
    rota_gestor,
    rota_admin,
)

from dependencies.autenticacao import (
    obter_usuario_autenticado,
    encerrar_sessao_por_token,
)


# =========================================================
# CONFIGURAÇÃO DA APLICAÇÃO
# =========================================================

app = FastAPI(
    title="THE IRON COMPASS",
    description="Sistema de gerenciamento de equipamentos e empréstimos",
    version="1.0.0",
)


# =========================================================
# ARQUIVOS ESTÁTICOS E TEMPLATES
# =========================================================

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static",
)

templates = Jinja2Templates(directory="templates")


# =========================================================
# REGISTRO DAS ROTAS
# =========================================================

app.include_router(rota_estoque.estoque_rota)
app.include_router(rota_equipamentos.equipamentos_rota)
app.include_router(rota_perfil.perfil_rota)
app.include_router(rota_usuarios.usuarios_rota)
app.include_router(rota_pedido.pedido_rota)
app.include_router(rota_emprestimos.emprestimos_rota)
app.include_router(rota_login.login_rota)

# Rotas do discente
app.include_router(rota_discente.discente_rota)

# Rotas do gestor
app.include_router(rota_gestor.gestor_rota)

# Rotas do administrador
app.include_router(rota_admin.admin_rota)


# =========================================================
# PREVENÇÃO DE CACHE
# =========================================================

def resposta_sem_cache(resposta):
    resposta.headers["Cache-Control"] = (
        "no-store, no-cache, must-revalidate, private, max-age=0"
    )
    resposta.headers["Pragma"] = "no-cache"
    resposta.headers["Expires"] = "0"

    return resposta


@app.middleware("http")
async def impedir_cache_respostas(request: Request, call_next):
    resposta = await call_next(request)
    return resposta_sem_cache(resposta)


# =========================================================
# REDIRECIONAMENTO PARA LOGIN
# =========================================================

def redirecionar_para_login():
    resposta = RedirectResponse(
        url="/login",
        status_code=status.HTTP_303_SEE_OTHER,
    )

    resposta.delete_cookie(
        key="access_token",
        path="/",
    )

    return resposta_sem_cache(resposta)


# =========================================================
# REDIRECIONAMENTO POR PERFIL
# =========================================================

def obter_dashboard_por_perfil(perfil: str):
    destinos = {
        "DISCENTE": "/dashboard-user",
        "GESTOR": "/dashboard-gestor",
        "ADMINISTRADOR": "/dashboard-admin",
    }

    return destinos.get(perfil)


# =========================================================
# ROTA INICIAL
# =========================================================

@app.get("/")
def root():
    return redirecionar_para_login()


# =========================================================
# PÁGINA DE LOGIN
# =========================================================

@app.get("/login")
def pagina_login(
    request: Request,
    db: Session = Depends(database.get_db),
):
    token = request.cookies.get("access_token")

    if token:
        try:
            encerrar_sessao_por_token(db, token)
        except SQLAlchemyError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Não foi possível encerrar a sessão. Tente novamente.",
            )

    resposta = templates.TemplateResponse(
        request=request,
        name="login.html",
        context={},
    )

    resposta.delete_cookie(
        key="access_token",
        path="/",
    )

    return resposta_sem_cache(resposta)


# =========================================================
# ENCERRAMENTO DE SESSÃO
# =========================================================

@app.post("/encerrar-sessao")
def encerrar_sessao(
    request: Request,
    db: Session = Depends(database.get_db),
):
    token = request.cookies.get("access_token")

    if token:
        try:
            encerrar_sessao_por_token(db, token)

        except SQLAlchemyError:
            db.rollback()

            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Não foi possível encerrar a sessão. Tente novamente.",
            )

    resposta = RedirectResponse(
        url="/login",
        status_code=status.HTTP_303_SEE_OTHER,
    )

    resposta.delete_cookie(
        key="access_token",
        path="/",
    )

    return resposta_sem_cache(resposta)


# =========================================================
# COMPATIBILIDADE COM FORMULÁRIOS ANTIGOS DE LOGOUT
# =========================================================

@app.post("/logout")
def logout(
    request: Request,
    db: Session = Depends(database.get_db),
):
    token = request.cookies.get("access_token")

    if token:
        try:
            encerrar_sessao_por_token(db, token)

        except SQLAlchemyError:
            db.rollback()

            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Não foi possível encerrar a sessão. Tente novamente.",
            )

    resposta = RedirectResponse(
        url="/login",
        status_code=status.HTTP_303_SEE_OTHER,
    )

    resposta.delete_cookie(
        key="access_token",
        path="/",
    )

    return resposta_sem_cache(resposta)