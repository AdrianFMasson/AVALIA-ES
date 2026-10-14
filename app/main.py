
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
from routes.rota_estoque import estoque_rota
from routes.rota_equipamentos import equipamentos_rota
from routes.rota_perfil import perfil_rota
from routes.rota_usuarios import usuarios_rota
from routes.rota_pedido import pedido_rota
from routes.rota_emprestimos import emprestimos_rota
from routes.rota_login import login_rota
from utils.autenticacao import validar_token_acesso, obter_sessao_ativa, encerrar_sessao_por_token

app = FastAPI(
    title="THE IRON COMPASS",
    description="Sistema de gerenciamento de equipamentos e empréstimos",
    version="1.0.0"
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(estoque_rota)
app.include_router(equipamentos_rota)
app.include_router(perfil_rota)
app.include_router(usuarios_rota)
app.include_router(pedido_rota)
app.include_router(emprestimos_rota)
app.include_router(login_rota)


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
        try:
            sessao.ativa = False
            db.add(sessao)
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
    resposta = RedirectResponse(
        url="/login",
        status_code=status.HTTP_303_SEE_OTHER
    )
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
                detail="Não foi possível encerrar a sessão anterior. Tente novamente."
            )

    resposta = templates.TemplateResponse(
        request=request,
        name="login.html",
        context={}
    )
    resposta.delete_cookie("access_token", path="/")
    return resposta_sem_cache(resposta)


@app.post("/encerrar-sessao")
def encerrar_sessao_navegacao(
    request: Request,
    db: Session = Depends(database.get_db)
):
    token = request.cookies.get("access_token")

    if token:
        try:
            encerrar_sessao_por_token(db, token)
        except SQLAlchemyError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Não foi possível encerrar a sessão. Tente novamente."
            )

    resposta = RedirectResponse(
        url="/login",
        status_code=status.HTTP_303_SEE_OTHER
    )
    resposta.delete_cookie("access_token", path="/")
    return resposta_sem_cache(resposta)


@app.get("/dashboard-user")
def dashboard_user(
    request: Request,
    db: Session = Depends(database.get_db)
):
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


@app.get("/dashboard-gestor")
def dashboard_gestor(
    request: Request,
    db: Session = Depends(database.get_db)
):
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
                detail="Não foi possível encerrar a sessão. Tente novamente."
            )

    resposta = RedirectResponse(
        url="/login",
        status_code=status.HTTP_303_SEE_OTHER
    )
    resposta.delete_cookie("access_token", path="/")
    return resposta_sem_cache(resposta)


@app.get("/config")
def config():
    return settings
