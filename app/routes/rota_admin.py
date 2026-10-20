from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlmodel import Session, select
from sqlalchemy import func

from dependencies.dependencies import database
from dependencies.autenticacao import obter_usuario_autenticado

from entities.models import (
    Usuarios,
    Perfil,
    Estoque,
    Equipamentos,
    Pedido,
    Emprestimos,
    StatusSolicitacao,
    StatusEquip,
    StatusPedido,
)

from config.Config import settings


admin_rota = APIRouter(tags=["Administrador"])
templates = Jinja2Templates(directory="templates")


# =========================================================
# ESQUEMAS DA API
# =========================================================

class EquipamentoEntrada(BaseModel):
    id_estoque: int
    nome: str
    categoria: str
    descricao: str | None = None
    status_equip: StatusEquip = StatusEquip.DISPONIVEL


class PedidoStatusEntrada(BaseModel):
    status: StatusPedido


# =========================================================
# AUTENTICAÇÃO
# =========================================================

def redirecionar_para_login():
    resposta = RedirectResponse(
        url="/login",
        status_code=status.HTTP_303_SEE_OTHER,
    )
    resposta.delete_cookie(key="access_token", path="/")
    return resposta


def exigir_admin(request: Request, db: Session):
    autenticacao = obter_usuario_autenticado(request, db)

    if autenticacao is None:
        return None

    if autenticacao["perfil"] != "ADMINISTRADOR":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seu perfil não tem permissão para acessar esta página.",
        )

    return autenticacao


def exigir_admin_api(request: Request, db: Session):
    autenticacao = exigir_admin(request, db)

    if autenticacao is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticação necessária ou sessão inválida.",
        )

    return autenticacao


def contexto_admin(autenticacao, **dados):
    return {"usuario": autenticacao["usuario"], **dados}


# =========================================================
# DASHBOARD
# =========================================================

@admin_rota.get("/dashboard-admin")
def dashboard_admin(
    request: Request,
    db: Session = Depends(database.get_db),
):
    autenticacao = exigir_admin(request, db)

    if autenticacao is None:
        return redirecionar_para_login()

    total_usuarios = db.exec(
        select(func.count()).select_from(Usuarios)
    ).one()

    total_equipamentos = db.exec(
        select(func.count()).select_from(Equipamentos)
    ).one()

    total_pedidos = db.exec(
        select(func.count()).select_from(Pedido)
    ).one()

    emprestimos_ativos = db.exec(
        select(func.count())
        .select_from(Emprestimos)
        .where(Emprestimos.status_solicitacao == StatusSolicitacao.APROVADO)
        .where(Emprestimos.data_devolucao.is_(None))
    ).one()

    pedidos_recentes = db.exec(
        select(Pedido).order_by(Pedido.data_pedido.desc()).limit(5)
    ).all()

    usuarios_recentes = db.exec(
        select(Usuarios).order_by(Usuarios.dt_cad_user.desc()).limit(5)
    ).all()

    equipamentos_recentes = db.exec(
        select(Equipamentos).order_by(Equipamentos.dt_cad_equip.desc()).limit(5)
    ).all()

    return templates.TemplateResponse(
        request=request,
        name="dashboard_admin.html",
        context=contexto_admin(
            autenticacao,
            total_usuarios=total_usuarios,
            total_equipamentos=total_equipamentos,
            total_pedidos=total_pedidos,
            emprestimos_ativos=emprestimos_ativos,
            pedidos_recentes=pedidos_recentes,
            usuarios_recentes=usuarios_recentes,
            equipamentos_recentes=equipamentos_recentes,
        ),
    )


# =========================================================
# USUÁRIOS
# =========================================================

@admin_rota.get("/admin_users")
def pagina_admin_usuarios(
    request: Request,
    db: Session = Depends(database.get_db),
):
    autenticacao = exigir_admin(request, db)

    if autenticacao is None:
        return redirecionar_para_login()

    usuarios = db.exec(select(Usuarios).order_by(Usuarios.nome)).all()
    perfis = db.exec(select(Perfil).order_by(Perfil.id_perfil)).all()

    return templates.TemplateResponse(
        request=request,
        name="admin_users.html",
        context=contexto_admin(
            autenticacao,
            usuarios=usuarios,
            perfis=perfis,
        ),
    )


@admin_rota.get("/api/admin/usuarios")
def api_admin_usuarios(
    request: Request,
    db: Session = Depends(database.get_db),
):
    exigir_admin_api(request, db)

    resultados = db.exec(
        select(Usuarios, Perfil)
        .join(Perfil, Usuarios.id_perfil == Perfil.id_perfil)
        .order_by(Usuarios.nome)
    ).all()

    return [
        {
            "id": usuario.id_usuario,
            "nome": usuario.nome,
            "email": usuario.email,
            "perfil": perfil.perfil.value,
            "ativo": usuario.ativo,
        }
        for usuario, perfil in resultados
    ]


# =========================================================
# EQUIPAMENTOS
# =========================================================

@admin_rota.get("/admin_equipamentos")
def pagina_admin_equipamentos(
    request: Request,
    db: Session = Depends(database.get_db),
):
    autenticacao = exigir_admin(request, db)

    if autenticacao is None:
        return redirecionar_para_login()

    equipamentos = db.exec(
        select(Equipamentos).order_by(Equipamentos.nome)
    ).all()

    estoques = db.exec(
        select(Estoque).order_by(Estoque.descricao)
    ).all()

    return templates.TemplateResponse(
        request=request,
        name="admin_equipamentos.html",
        context=contexto_admin(
            autenticacao,
            equipamentos=equipamentos,
            estoques=estoques,
        ),
    )


def validar_estoque(db: Session, id_estoque: int):
    estoque = db.get(Estoque, id_estoque)

    if estoque is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O estoque informado não existe.",
        )

    return estoque


def serializar_equipamento(equipamento, estoque):
    return {
        "id": equipamento.id_equipamento,
        "id_equipamento": equipamento.id_equipamento,
        "id_estoque": equipamento.id_estoque,
        "estoque": estoque.descricao,
        "nome": equipamento.nome,
        "categoria": equipamento.categoria,
        "descricao": equipamento.descricao,
        "status_equip": equipamento.status_equip.value,
    }


@admin_rota.get("/api/admin/equipamentos")
def api_listar_equipamentos(
    request: Request,
    db: Session = Depends(database.get_db),
):
    exigir_admin_api(request, db)

    resultados = db.exec(
        select(Equipamentos, Estoque)
        .join(Estoque, Equipamentos.id_estoque == Estoque.id_estoque)
        .order_by(Equipamentos.nome)
    ).all()

    return [
        serializar_equipamento(equipamento, estoque)
        for equipamento, estoque in resultados
    ]


@admin_rota.post(
    "/api/admin/equipamentos",
    status_code=status.HTTP_201_CREATED,
)
def api_criar_equipamento(
    dados: EquipamentoEntrada,
    request: Request,
    db: Session = Depends(database.get_db),
):
    exigir_admin_api(request, db)
    validar_estoque(db, dados.id_estoque)

    nome = dados.nome.strip()
    categoria = dados.categoria.strip()

    if not nome or not categoria:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Nome e categoria são obrigatórios.",
        )

    equipamento = Equipamentos(
        id_estoque=dados.id_estoque,
        nome=nome,
        categoria=categoria,
        descricao=dados.descricao.strip() if dados.descricao and dados.descricao.strip() else None,
        status_equip=dados.status_equip,
    )

    try:
        db.add(equipamento)
        db.commit()
        db.refresh(equipamento)

        estoque = db.get(Estoque, equipamento.id_estoque)
        return serializar_equipamento(equipamento, estoque)
    except Exception:
        db.rollback()
        raise


@admin_rota.put("/api/admin/equipamentos/{id_equipamento}")
def api_editar_equipamento(
    id_equipamento: int,
    dados: EquipamentoEntrada,
    request: Request,
    db: Session = Depends(database.get_db),
):
    exigir_admin_api(request, db)

    equipamento = db.get(Equipamentos, id_equipamento)

    if equipamento is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipamento não encontrado.",
        )

    estoque = db.get(Estoque, dados.id_estoque)

    if estoque is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O estoque informado não existe.",
        )

    nome = dados.nome.strip()
    categoria = dados.categoria.strip()

    if not nome or not categoria:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Nome e categoria são obrigatórios.",
        )

    equipamento.id_estoque = dados.id_estoque
    equipamento.nome = nome
    equipamento.categoria = categoria
    equipamento.descricao = (
        dados.descricao.strip()
        if dados.descricao and dados.descricao.strip()
        else None
    )
    equipamento.status_equip = dados.status_equip

    try:
        db.add(equipamento)
        db.commit()
        db.refresh(equipamento)

        estoque_atual = db.get(Estoque, equipamento.id_estoque)

        return serializar_equipamento(
            equipamento,
            estoque_atual,
        )

    except Exception:
        db.rollback()
        raise

    # =========================================================
# PÁGINA DE PEDIDOS
# =========================================================

@admin_rota.get("/admin_pedidos")
def pagina_admin_pedidos(
    request: Request,
    db: Session = Depends(database.get_db),
):
    autenticacao = exigir_admin(request, db)

    if autenticacao is None:
        return redirecionar_para_login()

    pedidos = db.exec(
        select(Pedido).order_by(Pedido.data_pedido.desc())
    ).all()

    return templates.TemplateResponse(
        request=request,
        name="admin_pedidos.html",
        context=contexto_admin(
            autenticacao,
            pedidos=pedidos,
        ),
    )


# =========================================================
# API DE PEDIDOS
# =========================================================

@admin_rota.get("/api/admin/pedidos")
def api_listar_pedidos(
    request: Request,
    db: Session = Depends(database.get_db),
):
    exigir_admin_api(request, db)

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


@admin_rota.patch("/api/admin/pedidos/{id_pedido}")
def api_atualizar_status_pedido(
    id_pedido: int,
    dados: PedidoStatusEntrada,
    request: Request,
    db: Session = Depends(database.get_db),
):
    exigir_admin_api(request, db)

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