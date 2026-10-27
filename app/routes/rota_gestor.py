from fastapi import (
    APIRouter,
    Request,
    Depends,
    HTTPException,
    status,
)
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlmodel import Session, select

from dependencies.dependencies import database
from dependencies.autenticacao import obter_usuario_autenticado
from entities.models import (
    Usuarios,
    Perfil,
    Equipamentos,
    Pedido,
    StatusPedido,
)


gestor_rota = APIRouter(tags=["Gestor"])
templates = Jinja2Templates(directory="templates")


# =========================================================
# AUTENTICAÇÃO E PERMISSÕES
# =========================================================

def redirecionar_para_login():
    resposta = RedirectResponse(
        url="/login",
        status_code=status.HTTP_303_SEE_OTHER,
    )
    resposta.delete_cookie("access_token", path="/")
    return resposta


def exigir_gestor(request: Request, db: Session):
    autenticacao = obter_usuario_autenticado(request, db)

    if autenticacao is None:
        return None

    if autenticacao["perfil"] != "GESTOR":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seu perfil não tem permissão para acessar esta página.",
        )

    return autenticacao


def exigir_gestor_api(request: Request, db: Session):
    autenticacao = exigir_gestor(request, db)

    if autenticacao is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticação necessária ou sessão inválida.",
        )

    return autenticacao


# =========================================================
# ENTRADA PARA ATUALIZAÇÃO DO STATUS
# =========================================================

class PedidoStatusEntrada(BaseModel):
    status: StatusPedido


# =========================================================
# PÁGINA DE EMPRÉSTIMOS DO GESTOR
# =========================================================

@gestor_rota.get("/gestor_emprestimos")
def gestor_emprestimos(
    request: Request,
    db: Session = Depends(database.get_db),
):
    autenticacao = exigir_gestor(request, db)

    if autenticacao is None:
        return redirecionar_para_login()

    return templates.TemplateResponse(
        request=request,
        name="gestor_emprestimos.html",
        context={
            "usuario": autenticacao["usuario"],
        },
    )


# =========================================================
# API: LISTAR SOLICITAÇÕES DE EMPRÉSTIMO
# =========================================================

@gestor_rota.get("/api/gestor/emprestimos")
def api_listar_emprestimos_gestor(
    request: Request,
    db: Session = Depends(database.get_db),
):
    exigir_gestor_api(request, db)

    resultados = db.exec(
        select(Pedido, Usuarios, Equipamentos)
        .join(
            Usuarios,
            Pedido.id_usuario == Usuarios.id_usuario,
        )
        .join(
            Equipamentos,
            Pedido.id_equipamento == Equipamentos.id_equipamento,
        )
        .order_by(Pedido.data_pedido.desc())
    ).all()

    return [
        {
            "id": pedido.id_pedido,
            "id_pedido": pedido.id_pedido,
            "id_usuario": usuario.id_usuario,
            "usuario": usuario.nome,
            "id_equipamento": equipamento.id_equipamento,
            "equipamento": equipamento.nome,
            "data_pedido": (
                pedido.data_pedido.isoformat()
                if pedido.data_pedido
                else None
            ),
            "status": pedido.status.value,
        }
        for pedido, usuario, equipamento in resultados
    ]


# =========================================================
# API: ATUALIZAR STATUS DA SOLICITAÇÃO
# =========================================================

@gestor_rota.patch("/api/gestor/emprestimos/{id_pedido}")
def api_atualizar_status_emprestimo_gestor(
    id_pedido: int,
    dados: PedidoStatusEntrada,
    request: Request,
    db: Session = Depends(database.get_db),
):
    exigir_gestor_api(request, db)

    pedido = db.get(Pedido, id_pedido)

    if pedido is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido não encontrado.",
        )

    pedido.status = dados.status

    try:
        db.add(pedido)
        db.commit()
        db.refresh(pedido)

        return {
            "id": pedido.id_pedido,
            "status": pedido.status.value,
            "mensagem": "Status do pedido atualizado com sucesso.",
        }

    except Exception:
        db.rollback()
        raise