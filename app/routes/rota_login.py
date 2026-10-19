from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlmodel import Session
from sqlalchemy.exc import SQLAlchemyError
from dependencies.dependencies import database
from controller import LoginController
from entities.models import UsuarioLogin
from utils.validacao_senha import validar_senha
from utils.autenticacao import criar_sessao
from config.Config import settings

login_rota = APIRouter(tags=["Autenticação"])


@login_rota.post("/api/login", status_code=status.HTTP_200_OK)
def realizar_login(
    dados: UsuarioLogin,
    request: Request,
    db: Session = Depends(database.get_db)
):
    senha_valida, mensagem = validar_senha(dados.senha)

    if not senha_valida:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=mensagem
        )

    try:
        usuario = LoginController.autenticar_usuario(
            db,
            dados.usuario,
            dados.senha
        )

        if not usuario or not isinstance(usuario, dict):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuário ou senha inválidos."
            )

        perfil = usuario.get("perfil")
        id_usuario = usuario.get("id_usuario")

        if not id_usuario:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Não foi possível identificar o usuário autenticado."
            )

        if perfil == "DISCENTE":
            destino = "/dashboard-user"
        elif perfil == "GESTOR":
            destino = "/dashboard-gestor"
        elif perfil == "ADMINISTRADOR":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="O acesso do administrador ainda não foi configurado."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Perfil sem permissão de acesso."
            )

        _, token = criar_sessao(db, id_usuario)

        resposta = JSONResponse(
            content={"url": destino},
            status_code=status.HTTP_200_OK
        )

        resposta.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            secure=request.url.scheme == "https",
            samesite="lax",
            max_age=settings.JWT_ACCESS_EXPIRE_MINUTES * 60,
            path="/"
        )

        resposta.headers["Cache-Control"] = (
            "no-store, no-cache, must-revalidate, private, max-age=0"
        )
        resposta.headers["Pragma"] = "no-cache"
        resposta.headers["Expires"] = "0"

        return resposta

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não foi possível autenticar com as credenciais informadas."
        )
    except (RuntimeError, SQLAlchemyError):
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível concluir a autenticação. Tente novamente."
        )