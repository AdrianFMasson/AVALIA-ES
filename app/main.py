from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlmodel import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi.responses import RedirectResponse, JSONResponse

from dependencies.dependencies import database
from dependencies.autenticacao import (
    obter_usuario_autenticado,
    encerrar_sessao_por_token,
)
from entities.models import Usuarios, Perfil
from routes import (
    rota_estoque,
    rota_equipamentos,
    rota_perfil,
    rota_usuarios,
    rota_pedido,
    rota_emprestimos,
    rota_login,
)
from controller import EmprestimosController


app = FastAPI(
    title="THE IRON COMPASS",
    description="Sistema de gerenciamento de equipamentos e empréstimos",
    version="1.0.0",
)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


# Registro das rotas
app.include_router(rota_estoque.estoque_rota)
app.include_router(rota_equipamentos.equipamentos_rota)
app.include_router(rota_perfil.perfil_rota)
app.include_router(rota_usuarios.usuarios_rota)
app.include_router(rota_pedido.pedido_rota)
app.include_router(rota_emprestimos.emprestimos_rota)
app.include_router(rota_login.login_rota)


# =========================================================
# CONTROLE DE CACHE
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
# AUTENTICAÇÃO E AUTORIZAÇÃO
# =========================================================

def exigir_autenticacao(request: Request, db: Session):
    autenticacao = obter_usuario_autenticado(request, db)

    if autenticacao is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticação necessária. Faça login para continuar.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return autenticacao


def exigir_perfil(autenticacao: dict, perfil_esperado: str):
    if autenticacao["perfil"] != perfil_esperado:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seu perfil não tem permissão para acessar esta página.",
        )


def redirecionar_para_login():
    resposta = RedirectResponse(
        url="/login",
        status_code=status.HTTP_303_SEE_OTHER,
    )
    resposta.delete_cookie("access_token", path="/")

    return resposta_sem_cache(resposta)


# =========================================================
# PÁGINA INICIAL
# =========================================================

@app.get("/")
def root():
    return redirecionar_para_login()


# =========================================================
# LOGIN
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
                detail="Não foi possível encerrar a sessão anterior.",
            )

    resposta = templates.TemplateResponse(
        request=request,
        name="login.html",
        context={},
    )

    resposta.delete_cookie("access_token", path="/")

    return resposta_sem_cache(resposta)


# =========================================================
# DASHBOARD DO DISCENTE
# =========================================================

@app.get("/dashboard-user")
def dashboard_user(
    request: Request,
    db: Session = Depends(database.get_db),
):
    autenticacao = exigir_autenticacao(request, db)
    exigir_perfil(autenticacao, "DISCENTE")

    resposta = templates.TemplateResponse(
        request=request,
        name="dashboard_user.html",
        context={
            "usuario": autenticacao["usuario"],
        },
    )

    return resposta_sem_cache(resposta)


# =========================================================
# PEDIDOS DO DISCENTE
# =========================================================

@app.get("/user_pedidos")
def user_pedidos(
    request: Request,
    db: Session = Depends(database.get_db),
):
    autenticacao = exigir_autenticacao(request, db)
    exigir_perfil(autenticacao, "DISCENTE")

    resposta = templates.TemplateResponse(
        request=request,
        name="user_pedidos.html",
        context={
            "usuario": autenticacao["usuario"],
        },
    )

    return resposta_sem_cache(resposta)


# =========================================================
# EMPRÉSTIMOS DO DISCENTE
# =========================================================

@app.get("/user_emprestimos")
def user_emprestimos(
    request: Request,
    db: Session = Depends(database.get_db),
):
    autenticacao = exigir_autenticacao(request, db)
    exigir_perfil(autenticacao, "DISCENTE")

    usuario = autenticacao["usuario"]

    try:
        emprestimos = EmprestimosController.buscar_emprestimos_usuario(
            db,
            usuario.id_usuario,
        )
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível consultar seus empréstimos. Tente novamente.",
        )

    resposta = templates.TemplateResponse(
        request=request,
        name="user_emprestimos.html",
        context={
            "usuario": usuario,
            "emprestimos": emprestimos,
        },
    )

    return resposta_sem_cache(resposta)


# =========================================================
# DASHBOARD DO GESTOR
# =========================================================

@app.get("/dashboard-gestor")
def dashboard_gestor(
    request: Request,
    db: Session = Depends(database.get_db),
):
    autenticacao = exigir_autenticacao(request, db)
    exigir_perfil(autenticacao, "GESTOR")

    resposta = templates.TemplateResponse(
        request=request,
        name="dashboard_gestor.html",
        context={
            "usuario": autenticacao["usuario"],
        },
    )

    return resposta_sem_cache(resposta)


# =========================================================
# USUÁRIOS DO GESTOR
# =========================================================

@app.get("/gestor_users")
def gestor_users(
    request: Request,
    db: Session = Depends(database.get_db),
):
    autenticacao = exigir_autenticacao(request, db)
    exigir_perfil(autenticacao, "GESTOR")

    resposta = templates.TemplateResponse(
        request=request,
        name="gestor_users.html",
        context={
            "usuario": autenticacao["usuario"],
        },
    )

    return resposta_sem_cache(resposta)


# =========================================================
# PERFIL DO DISCENTE
# =========================================================

@app.get("/user_perfil")
def user_perfil(
    request: Request,
    db: Session = Depends(database.get_db),
):
    autenticacao = exigir_autenticacao(request, db)
    exigir_perfil(autenticacao, "DISCENTE")

    resposta = templates.TemplateResponse(
        request=request,
        name="user_perfil.html",
        context={
            "usuario": autenticacao["usuario"],
        },
    )

    return resposta_sem_cache(resposta)


# =========================================================
# EDIÇÃO DE USUÁRIO PELO GESTOR
# =========================================================

@app.get("/gestor/usuarios/editar/{usuario_id}")
def editar_usuario(
    usuario_id: int,
    request: Request,
    db: Session = Depends(database.get_db),
):
    autenticacao = exigir_autenticacao(request, db)
    exigir_perfil(autenticacao, "GESTOR")

    usuario = db.get(Usuarios, usuario_id)

    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado.",
        )

    perfil_usuario = db.get(Perfil, usuario.id_perfil)

    if (
        perfil_usuario is None
        or perfil_usuario.perfil.value != "DISCENTE"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Somente usuários com perfil DISCENTE "
                "podem ser editados nesta página."
            ),
        )

    resposta = templates.TemplateResponse(
        request=request,
        name="gestor_users_editar.html",
        context={
            "usuario": autenticacao["usuario"],
            "discente": usuario,
        },
    )

    return resposta_sem_cache(resposta)


# =========================================================
# EQUIPAMENTOS DO GESTOR
# =========================================================

@app.get("/gestor_equipamentos")
def gestor_equipamentos(
    request: Request,
    db: Session = Depends(database.get_db),
):
    autenticacao = exigir_autenticacao(request, db)
    exigir_perfil(autenticacao, "GESTOR")

    resposta = templates.TemplateResponse(
        request=request,
        name="gestor_equipamentos.html",
        context={
            "usuario": autenticacao["usuario"],
        },
    )

    return resposta_sem_cache(resposta)


# =========================================================
# ENCERRAMENTO DE SESSÃO (LOGOUT)
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
                detail="Não foi possível encerrar a sessão.",
            )

    resposta = RedirectResponse(
        url="/login",
        status_code=status.HTTP_303_SEE_OTHER,
    )

    resposta.delete_cookie("access_token", path="/")

    return resposta_sem_cache(resposta)


# =========================================================
# PEDIDOS DO GESTOR
# =========================================================

@app.get("/gestor_pedidos")
def gestor_pedidos(
    request: Request,
    db: Session = Depends(database.get_db),
):
    autenticacao = exigir_autenticacao(request, db)
    exigir_perfil(autenticacao, "GESTOR")

    resposta = templates.TemplateResponse(
        request=request,
        name="gestor_pedidos.html",
        context={
            "usuario": autenticacao["usuario"],
        },
    )

    return resposta_sem_cache(resposta)


# =========================================================
# EDIÇÃO DE PEDIDO PELO GESTOR
# =========================================================

@app.get("/gestor/pedidos/editar/{pedido_id}")
def gestor_pedidos_editar(
    pedido_id: int,
    request: Request,
    db: Session = Depends(database.get_db),
):
    autenticacao = exigir_autenticacao(request, db)
    exigir_perfil(autenticacao, "GESTOR")

    resposta = templates.TemplateResponse(
        request=request,
        name="gestor_pedidos_editar.html",
        context={
            "usuario": autenticacao["usuario"],
            "pedido_id": pedido_id,
        },
    )

    return resposta_sem_cache(resposta)


# =========================================================
# CONFIGURAÇÕES — ADMINISTRADOR
# =========================================================

@app.get("/config")
def config(
    request: Request,
    db: Session = Depends(database.get_db),
):
    autenticacao = exigir_autenticacao(request, db)
    exigir_perfil(autenticacao, "ADMINISTRADOR")

    resposta = JSONResponse(
        content={
            "aplicacao": "THE IRON COMPASS",
            "versao": "1.0.0",
        }
    )

    return resposta_sem_cache(resposta)