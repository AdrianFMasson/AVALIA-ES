
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlmodel import Session, select
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from pathlib import Path

from dependencies.dependencies import database
from dependencies.autenticacao import obter_usuario_autenticado

from entities.models import (
    Usuarios,
    Perfil,
    Estoque,
    Categoria,
    Equipamentos,
    Pedido,
    Emprestimos,
    StatusSolicitacao,
    StatusEquip,
    StatusPedido,
)


admin_rota = APIRouter(tags=["Administrador"])

BASE_DIR = Path(__file__).resolve().parent.parent

templates = Jinja2Templates(
    directory=str(BASE_DIR / "templates")
)


# =========================================================
# ESQUEMAS DA API
# =========================================================

class EquipamentoEntrada(BaseModel):
    id_estoque: int
    id_categoria: int
    nome: str
    descricao: str | None = None
    status_equip: StatusEquip = StatusEquip.DISPONIVEL


class PedidoStatusEntrada(BaseModel):
    status: StatusPedido


class CategoriaEntrada(BaseModel):
    nome: str
    descricao: str | None = None


class CategoriaStatusEntrada(BaseModel):
    ativo: bool


# =========================================================
# AUTENTICAÇÃO
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
    return {
        "usuario": autenticacao["usuario"],
        **dados,
    }


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
        .where(
            Emprestimos.status_solicitacao
            == StatusSolicitacao.APROVADO
        )
        .where(Emprestimos.data_devolucao.is_(None))
    ).one()

    pedidos_recentes = db.exec(
        select(Pedido)
        .order_by(Pedido.data_pedido.desc())
        .limit(5)
    ).all()

    usuarios_recentes = db.exec(
        select(Usuarios)
        .order_by(Usuarios.dt_cad_user.desc())
        .limit(5)
    ).all()

    equipamentos_recentes = db.exec(
        select(Equipamentos)
        .order_by(Equipamentos.dt_cad_equip.desc())
        .limit(5)
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

    usuarios = db.exec(
        select(Usuarios).order_by(Usuarios.nome)
    ).all()

    perfis = db.exec(
        select(Perfil).order_by(Perfil.id_perfil)
    ).all()

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
        .join(
            Perfil,
            Usuarios.id_perfil == Perfil.id_perfil,
        )
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
        select(Equipamentos)
        .order_by(Equipamentos.nome)
    ).all()

    estoques = db.exec(
        select(Estoque)
        .order_by(Estoque.descricao)
    ).all()

    categorias = db.exec(
        select(Categoria)
        .where(Categoria.ativo == True)
        .order_by(Categoria.nome)
    ).all()

    return templates.TemplateResponse(
        request=request,
        name="admin_equipamentos.html",
        context=contexto_admin(
            autenticacao,
            equipamentos=equipamentos,
            estoques=estoques,
            categorias=categorias,
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


def validar_categoria(
    db: Session,
    id_categoria: int,
):
    categoria = db.get(Categoria, id_categoria)

    if categoria is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A categoria informada não existe.",
        )

    if not categoria.ativo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A categoria selecionada está inativa.",
        )

    return categoria


def serializar_equipamento(
    equipamento,
    estoque,
    categoria,
):
    return {
        "id": equipamento.id_equipamento,
        "id_equipamento": equipamento.id_equipamento,
        "id_estoque": equipamento.id_estoque,
        "estoque": estoque.descricao,
        "id_categoria": equipamento.id_categoria,
        "categoria": categoria.nome,
        "nome": equipamento.nome,
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
        select(
            Equipamentos,
            Estoque,
            Categoria,
        )
        .join(
            Estoque,
            Equipamentos.id_estoque == Estoque.id_estoque,
        )
        .join(
            Categoria,
            Equipamentos.id_categoria == Categoria.id_categoria,
        )
        .order_by(Equipamentos.nome)
    ).all()

    return [
        serializar_equipamento(
            equipamento,
            estoque,
            categoria,
        )
        for equipamento, estoque, categoria in resultados
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

    validar_estoque(
        db,
        dados.id_estoque,
    )

    categoria = validar_categoria(
        db,
        dados.id_categoria,
    )

    nome = dados.nome.strip()

    if not nome:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="O nome do equipamento é obrigatório.",
        )

    equipamento = Equipamentos(
        id_estoque=dados.id_estoque,
        id_categoria=dados.id_categoria,

        # Mantém compatibilidade com a coluna antiga
        # enquanto a migração não for concluída.
        categoria=categoria.nome,

        nome=nome,

        descricao=(
            dados.descricao.strip()
            if dados.descricao and dados.descricao.strip()
            else None
        ),

        status_equip=dados.status_equip,
    )

    try:
        db.add(equipamento)
        db.commit()
        db.refresh(equipamento)

        estoque = db.get(
            Estoque,
            equipamento.id_estoque,
        )

        return serializar_equipamento(
            equipamento,
            estoque,
            categoria,
        )

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não foi possível cadastrar o equipamento. Verifique os dados informados.",
        )

    except Exception:
        db.rollback()
        raise


@admin_rota.put(
    "/api/admin/equipamentos/{id_equipamento}"
)
def api_editar_equipamento(
    id_equipamento: int,
    dados: EquipamentoEntrada,
    request: Request,
    db: Session = Depends(database.get_db),
):
    exigir_admin_api(request, db)

    equipamento = db.get(
        Equipamentos,
        id_equipamento,
    )

    if equipamento is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipamento não encontrado.",
        )

    validar_estoque(
        db,
        dados.id_estoque,
    )

    categoria = validar_categoria(
        db,
        dados.id_categoria,
    )

    nome = dados.nome.strip()

    if not nome:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="O nome do equipamento é obrigatório.",
        )

    equipamento.id_estoque = dados.id_estoque
    equipamento.id_categoria = dados.id_categoria
    equipamento.nome = nome

    # Atualiza também a coluna antiga.
    equipamento.categoria = categoria.nome

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

        estoque_atual = db.get(
            Estoque,
            equipamento.id_estoque,
        )

        return serializar_equipamento(
            equipamento,
            estoque_atual,
            categoria,
        )

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não foi possível atualizar o equipamento. Verifique os dados informados.",
        )

    except Exception:
        db.rollback()
        raise


# =========================================================
# CATEGORIAS
# =========================================================

def validar_nome_categoria(
    db: Session,
    nome: str,
    id_categoria: int | None = None,
):
    nome = nome.strip()

    if not nome:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="O nome da categoria é obrigatório.",
        )

    consulta = select(Categoria).where(
        func.lower(Categoria.nome) == nome.lower()
    )

    if id_categoria is not None:
        consulta = consulta.where(
            Categoria.id_categoria != id_categoria
        )

    categoria_existente = db.exec(
        consulta
    ).first()

    if categoria_existente is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe uma categoria com esse nome.",
        )

    return nome


def serializar_categoria(categoria):
    return {
        "id": categoria.id_categoria,
        "id_categoria": categoria.id_categoria,
        "nome": categoria.nome,
        "descricao": categoria.descricao,
        "ativo": categoria.ativo,
        "dt_cad_categoria": (
            categoria.dt_cad_categoria.isoformat()
            if categoria.dt_cad_categoria
            else None
        ),
    }


@admin_rota.get("/api/admin/categorias")
def api_listar_categorias(
    request: Request,
    db: Session = Depends(database.get_db),
):
    exigir_admin_api(request, db)

    categorias = db.exec(
        select(Categoria)
        .order_by(Categoria.nome)
    ).all()

    return [
        serializar_categoria(categoria)
        for categoria in categorias
    ]


@admin_rota.post(
    "/api/admin/categorias",
    status_code=status.HTTP_201_CREATED,
)
def api_criar_categoria(
    dados: CategoriaEntrada,
    request: Request,
    db: Session = Depends(database.get_db),
):
    exigir_admin_api(request, db)

    nome = validar_nome_categoria(
        db,
        dados.nome,
    )

    descricao = (
        dados.descricao.strip()
        if dados.descricao and dados.descricao.strip()
        else None
    )

    categoria = Categoria(
        nome=nome,
        descricao=descricao,
        ativo=True,
    )

    try:
        db.add(categoria)
        db.commit()
        db.refresh(categoria)

        return serializar_categoria(categoria)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe uma categoria com esse nome.",
        )

    except Exception:
        db.rollback()
        raise


@admin_rota.put(
    "/api/admin/categorias/{id_categoria}"
)
def api_editar_categoria(
    id_categoria: int,
    dados: CategoriaEntrada,
    request: Request,
    db: Session = Depends(database.get_db),
):
    exigir_admin_api(request, db)

    categoria = db.get(
        Categoria,
        id_categoria,
    )

    if categoria is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoria não encontrada.",
        )

    nome = validar_nome_categoria(
        db,
        dados.nome,
        id_categoria=id_categoria,
    )

    categoria.nome = nome

    categoria.descricao = (
        dados.descricao.strip()
        if dados.descricao and dados.descricao.strip()
        else None
    )

    try:
        # Atualiza o campo antigo dos equipamentos
        # vinculados a esta categoria.
        equipamentos_vinculados = db.exec(
            select(Equipamentos).where(
                Equipamentos.id_categoria == id_categoria
            )
        ).all()

        for equipamento in equipamentos_vinculados:
            equipamento.categoria = nome

        db.add(categoria)
        db.commit()
        db.refresh(categoria)

        return serializar_categoria(categoria)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe uma categoria com esse nome.",
        )

    except Exception:
        db.rollback()
        raise


@admin_rota.patch(
    "/api/admin/categorias/{id_categoria}/status"
)
def api_alterar_status_categoria(
    id_categoria: int,
    dados: CategoriaStatusEntrada,
    request: Request,
    db: Session = Depends(database.get_db),
):
    exigir_admin_api(request, db)

    categoria = db.get(
        Categoria,
        id_categoria,
    )

    if categoria is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoria não encontrada.",
        )

    categoria.ativo = dados.ativo

    try:
        db.add(categoria)
        db.commit()
        db.refresh(categoria)

        return {
            "id": categoria.id_categoria,
            "ativo": categoria.ativo,
            "mensagem": (
                "Categoria ativada com sucesso."
                if categoria.ativo
                else "Categoria desativada com sucesso."
            ),
        }

    except Exception:
        db.rollback()
        raise


@admin_rota.get("/admin_categorias")
def pagina_admin_categorias(
    request: Request,
    db: Session = Depends(database.get_db),
):
    autenticacao = exigir_admin(request, db)

    if autenticacao is None:
        return redirecionar_para_login()

    return templates.TemplateResponse(
        request=request,
        name="admin_categorias.html",
        context=contexto_admin(autenticacao),
    )


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
        select(Pedido)
        .order_by(Pedido.data_pedido.desc())
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
        select(
            Pedido,
            Usuarios,
            Equipamentos,
        )
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


@admin_rota.patch(
    "/api/admin/pedidos/{id_pedido}"
)
def api_atualizar_status_pedido(
    id_pedido: int,
    dados: PedidoStatusEntrada,
    request: Request,
    db: Session = Depends(database.get_db),
):
    exigir_admin_api(request, db)

    pedido = db.get(
        Pedido,
        id_pedido,
    )

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
