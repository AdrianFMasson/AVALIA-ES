from typing import List
from sqlmodel import Session, select
from sqlalchemy.exc import OperationalError, IntegrityError
from entities.models import Usuarios, Perfil, UsuarioAtualizacao
from utils.validacao_senha import validar_senha
from utils.seguranca_senha import gerar_hash_senha

def buscar_usuario_por_id(db: Session, usuario_id: int) -> Usuarios | None:
    try:
        return db.get(Usuarios, usuario_id)
    except OperationalError as e:
        raise RuntimeError(
            "Falha de comunicação com o banco de dados."
        ) from e

def buscar_usuarios(db: Session) -> List[Usuarios]:
    try:
        statement = select(Usuarios)
        return db.exec(statement).all()
    except OperationalError as e:
        raise RuntimeError("Falha de comunicação com o banco de dados.") from e

def cadastrar_usuario(db: Session, dados: Usuarios) -> Usuarios:
    try:
        perfil = db.get(Perfil, dados.id_perfil)
        if perfil is None:
            raise ValueError("O perfil informado não está cadastrado no sistema.")

        novo_usuario = Usuarios(**dados.model_dump())
        db.add(novo_usuario)
        db.commit()
        db.refresh(novo_usuario)
        return novo_usuario
    except IntegrityError as e:
        db.rollback()
        raise ValueError("Erro nos dados informados. Verifique e tente novamente.") from e
    except OperationalError as e:
        db.rollback()
        print("ERRO DO BANCO:")
        print(e)
        print("CAUSA ORIGINAL:")
        print(e.orig)
        raise RuntimeError(f"Erro do banco de dados: {e.orig}") from e

def atualizar_usuario(db: Session, usuario_id: int, dados: UsuarioAtualizacao) -> Usuarios:
    try:
        usuario = db.get(Usuarios, usuario_id)
        if usuario is None:
            raise KeyError(f"Usuário de ID {usuario_id} não encontrado.")

        perfil = db.get(Perfil, dados.id_perfil)
        if perfil is None:
            raise ValueError("O perfil informado não está cadastrado no sistema.")

        usuario.nome = dados.nome
        usuario.contato = dados.contato
        usuario.email = str(dados.email)
        usuario.id_perfil = dados.id_perfil
        usuario.ativo = dados.ativo

        if dados.senha and dados.senha.strip():
            senha_valida, mensagem = validar_senha(dados.senha)
            if not senha_valida:
                raise ValueError(mensagem)
            usuario.senha_hash = gerar_hash_senha(dados.senha)

        db.add(usuario)
        db.commit()
        db.refresh(usuario)
        return usuario
    except (IntegrityError, OperationalError) as e:
        db.rollback()
        if isinstance(e, IntegrityError):
            raise ValueError("Erro de integridade nos dados informados.") from e
        raise RuntimeError("Falha de comunicação com o banco de dados.") from e

def deletar_usuario(db: Session, usuario_id: int):
    try:
        usuario = db.get(Usuarios, usuario_id)
        if usuario is None:
            raise KeyError(f"Usuário de ID {usuario_id} não encontrado.")

        db.delete(usuario)
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise ValueError("Não foi possível excluir o usuário.") from e
    except OperationalError as e:
        db.rollback()
        raise RuntimeError("Falha de comunicação com o banco de dados.") from e