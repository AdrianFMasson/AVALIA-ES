
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from jwt import InvalidTokenError
from sqlmodel import Session
from sqlalchemy.exc import SQLAlchemyError

from config.Config import settings
from dependencies.dependencies import database
from entities.models import Usuarios, Perfil
from routes import rota_estoque, rota_equipamentos, rota_perfil, rota_usuarios, rota_pedido, rota_emprestimos, rota_login
from controller import EmprestimosController
from utils.autenticacao import validar_token_acesso, obter_sessao_ativa, encerrar_sessao_por_token

app = FastAPI(
    title="THE IRON COMPASS",
    description="Sistema de gerenciamento de equipamentos e empréstimos",
    version="1.0.0"
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(rota_estoque.estoque_rota)
app.include_router(rota_equipamentos.equipamentos_rota)
app.include_router(rota_perfil.perfil_rota)
app.include_router(rota_usuarios.usuarios_rota)
app.include_router(rota_pedido.pedido_rota)
app.include_router(rota_emprestimos.emprestimos_rota)
app.include_router(rota_login.login_rota)

def resposta_sem_cache(resposta):
    resposta.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private, max-age=0"
    resposta.headers["Pragma"] = "no-cache"
    resposta.headers["Expires"] = "0"
    return resposta

@app.middleware("http")
async def impedir_cache_respostas(request: Request, call_next):
    resposta = await call_next(request)
    return resposta_sem_cache(resposta)

def obter_usuario_autenticado(request: Request, db: Session):
    token = request.cookies.get("access_token")
    if not token:
        return None

    try:
        payload = validar_token_acesso(token)
        id_usuario = int(payload["sub"])
        id_sessao = payload["sid"]
    except (InvalidTokenError, ValueError, KeyError, TypeError):
        return None

    try:
        sessao = obter_sessao_ativa(db, id_sessao, id_usuario)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível validar a sessão. Tente novamente."
        )

    if sessao is None:
        return None

    usuario = db.get(Usuarios, id_usuario)

    if usuario is None or not usuario.ativo:
        sessao.ativa = False
        db.add(sessao)
        try:
            db.commit()
        except SQLAlchemyError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Não foi possível validar a sessão. Tente novamente."
            )
        return None

    perfil = db.get(Perfil, usuario.id_perfil)
    if perfil is None:
        return None

    return {
        "usuario": usuario,
        "perfil": perfil.perfil.value
    }

def redirecionar_para_login():
    resposta = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    resposta.delete_cookie("access_token", path="/")
    return resposta_sem_cache(resposta)

@app.get("/")
def root():
    return redirecionar_para_login()

@app.get("/login")
def pagina_login(request: Request, db: Session = Depends(database.get_db)):
    token = request.cookies.get("access_token")

    if token:
        try:
            encerrar_sessao_por_token(db, token)
        except SQLAlchemyError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Não foi possível encerrar a sessão anterior."
            )

    resposta = templates.TemplateResponse(
        request=request,
        name="login.html",
        context={}
    )
    resposta.delete_cookie("access_token", path="/")
    return resposta_sem_cache(resposta)

@app.get("/dashboard-user")
def dashboard_user(request: Request, db: Session = Depends(database.get_db)):
    autenticacao = obter_usuario_autenticado(request, db)

    if autenticacao is None:
        return redirecionar_para_login()

    if autenticacao["perfil"] != "DISCENTE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seu perfil não tem permissão para acessar este dashboard."
        )

    resposta = templates.TemplateResponse(
        request=request,
        name="dashboard_user.html",
        context={"usuario": autenticacao["usuario"]}
    )
    return resposta_sem_cache(resposta)

@app.get("/user_pedidos")
def user_pedidos(request: Request, db: Session = Depends(database.get_db)):
    autenticacao = obter_usuario_autenticado(request, db)

    if autenticacao is None:
        return redirecionar_para_login()

    if autenticacao["perfil"] != "DISCENTE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seu perfil não tem permissão para acessar os pedidos do usuário."
        )

    resposta = templates.TemplateResponse(
        request=request,
        name="user_pedidos.html",
        context={"usuario": autenticacao["usuario"]}
    )
    return resposta_sem_cache(resposta)

@app.get("/user_emprestimos")
def user_emprestimos(request: Request, db: Session = Depends(database.get_db)):
    autenticacao = obter_usuario_autenticado(request, db)

    if autenticacao is None:
        return redirecionar_para_login()

    if autenticacao["perfil"] != "DISCENTE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seu perfil não tem permissão para acessar os empréstimos do usuário."
        )

    usuario = autenticacao["usuario"]

    try:
        emprestimos = EmprestimosController.buscar_emprestimos_usuario(
            db,
            usuario.id_usuario
        )
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível consultar seus empréstimos. Tente novamente."
        )

    resposta = templates.TemplateResponse(
        request=request,
        name="user_emprestimos.html",
        context={
            "usuario": usuario,
            "emprestimos": emprestimos
        }
    )
    return resposta_sem_cache(resposta)

@app.get("/dashboard-gestor")
def dashboard_gestor(request: Request, db: Session = Depends(database.get_db)):
    autenticacao = obter_usuario_autenticado(request, db)

    if autenticacao is None:
        return redirecionar_para_login()

    if autenticacao["perfil"] != "GESTOR":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seu perfil não tem permissão para acessar este dashboard."
        )

    resposta = templates.TemplateResponse(
        request=request,
        name="dashboard_gestor.html",
        context={"usuario": autenticacao["usuario"]}
    )
    return resposta_sem_cache(resposta)

@app.post("/encerrar-sessao")
def encerrar_sessao(request: Request, db: Session = Depends(database.get_db)):
    token = request.cookies.get("access_token")

    if token:
        try:
            encerrar_sessao_por_token(db, token)
        except SQLAlchemyError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Não foi possível encerrar a sessão."
            )

    resposta = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    resposta.delete_cookie("access_token", path="/")
    return resposta_sem_cache(resposta)

@app.post("/logout")
def logout(request: Request, db: Session = Depends(database.get_db)):
    token = request.cookies.get("access_token")

    if token:
        try:
            encerrar_sessao_por_token(db, token)
        except SQLAlchemyError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Não foi possível encerrar a sessão."
            )

    resposta = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    resposta.delete_cookie("access_token", path="/")
    return resposta_sem_cache(resposta)

@app.get("/config")
def config():
    return settings
