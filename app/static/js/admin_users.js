"use strict";

const API_USUARIOS = "/api/admin/usuarios";

const elementos = {
    lista: document.getElementById("listaUsuarios"),
    busca: document.getElementById("buscaUsuarios"),
    filtro: document.getElementById("filtroStatus"),
    mensagem: document.getElementById("mensagemUsuarios"),
    modal: document.getElementById("modalUsuario"),
    formulario: document.getElementById("formUsuario"),
    tituloModal: document.getElementById("tituloModal"),
    id: document.getElementById("usuarioId"),
    nome: document.getElementById("nomeUsuario"),
    email: document.getElementById("emailUsuario"),
    perfil: document.getElementById("perfilUsuario"),
    ativo: document.getElementById("statusUsuario"),
    senha: document.getElementById("senhaUsuario"),
    erro: document.getElementById("erroFormulario")
};

let usuarios = [];

function escapar(valor) {
    return String(valor ?? "").replace(/[&<>"']/g, caractere => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "'"
    })[caractere]);
}

function atualizarIndicadores() {
    const total = document.getElementById("totalUsuarios");
    const ativos = document.getElementById("usuariosAtivos");
    const inativos = document.getElementById("usuariosInativos");

    if (total) {
        total.textContent = usuarios.length;
    }

    if (ativos) {
        ativos.textContent = usuarios.filter(
            usuario => usuario.ativo
        ).length;
    }

    if (inativos) {
        inativos.textContent = usuarios.filter(
            usuario => !usuario.ativo
        ).length;
    }
}

function renderizarUsuarios() {
    if (!elementos.lista || !elementos.busca || !elementos.filtro) {
        console.error("Elementos da tabela de usuários não encontrados.");
        return;
    }

    const termo = elementos.busca.value
        .trim()
        .toLocaleLowerCase("pt-BR");

    const filtroStatus = elementos.filtro.value;

    const filtrados = usuarios.filter(usuario => {
        const correspondeTexto =
            `${usuario.nome} ${usuario.email}`
                .toLocaleLowerCase("pt-BR")
                .includes(termo);

        const correspondeStatus =
            !filtroStatus ||
            (
                filtroStatus === "ativo"
                    ? usuario.ativo
                    : !usuario.ativo
            );

        return correspondeTexto && correspondeStatus;
    });

    elementos.lista.innerHTML = filtrados.map(usuario => `
        <tr>
            <td>${escapar(usuario.nome)}</td>
            <td>${escapar(usuario.email)}</td>
            <td>${escapar(usuario.perfil)}</td>
            <td>
                <span class="status ${usuario.ativo ? "ativo" : "inativo"}">
                    ${usuario.ativo ? "Ativo" : "Inativo"}
                </span>
            </td>
            <td>
                <button
                    type="button"
                    class="acao"
                    data-editar="${escapar(usuario.id)}">
                    Editar
                </button>

                <button
                    type="button"
                    class="acao"
                    data-alternar="${escapar(usuario.id)}">
                    ${usuario.ativo ? "Desativar" : "Ativar"}
                </button>
            </td>
        </tr>
    `).join("");

    if (elementos.mensagem) {
        elementos.mensagem.textContent = filtrados.length
            ? ""
            : "Nenhum usuário encontrado.";
    }

    atualizarIndicadores();
}

async function carregarUsuarios() {
    if (!elementos.lista || !elementos.mensagem) {
        console.error("Tabela ou mensagem de usuários não encontrada.");
        return Promise.resolve();
    }

    elementos.mensagem.textContent = "Carregando usuários...";
    elementos.lista.innerHTML = "";

    return fetch(API_USUARIOS, {
        method: "GET",
        credentials: "same-origin",
        headers: {
            "Accept": "application/json"
        }
    })
    .then(resposta => {
        if (resposta.status === 401 || resposta.status === 403) {
            window.location.assign("/login");
            return null;
        }

        if (!resposta.ok) {
            throw new Error(
                `Falha ao consultar usuários (HTTP ${resposta.status}).`
            );
        }

        return resposta.json();
    })
    .then(dados => {
        if (!dados) return;

        if (!Array.isArray(dados)) {
            throw new Error("A API retornou uma lista inválida.");
        }

        usuarios = dados.map(usuario => ({
            id: usuario.id,
            nome: usuario.nome ?? "",
            email: usuario.email ?? "",
            perfil: usuario.perfil ?? "Não definido",
            ativo: Boolean(usuario.ativo)
        }));

        renderizarUsuarios();
    })
    .catch(erro => {
        console.error("Erro ao carregar usuários:", erro);

        elementos.lista.innerHTML = "";
        elementos.mensagem.textContent =
            "Não foi possível carregar os usuários. Verifique a conexão com o servidor.";

            throw erro;
    });
}

async function salvarUsuario(evento) {
    evento.preventDefault();
    mostrarErroFormulario("");

    const id = elementos.id.value.trim();
    const editando = Boolean(id);

    const payload = {
        nome: elementos.nome.value.trim(),
        email: elementos.email.value.trim(),
        perfil: elementos.perfil.value.trim().toUpperCase(),
        ativo: elementos.ativo.value === "true"
    };

    if (elementos.senha.value) {
        payload.senha = elementos.senha.value;
    }

    const perfisValidos = ["DISCENTE", "GESTOR", "ADMINISTRADOR"];

    if (!perfisValidos.includes(payload.perfil)) {
        mostrarErroFormulario("Selecione um perfil válido.");
        elementos.perfil.focus();
        return;
    }

    const url = editando
        ? `${API_USUARIOS}/${id}`
        : API_USUARIOS;

    const metodo = editando ? "PUT" : "POST";

    try {
        const resposta = await fetch(url, {
            method: metodo,
            credentials: "same-origin",
            headers: {
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            body: JSON.stringify(payload)
        });

        const dados = await resposta.json().catch(() => null);

        if (resposta.status === 401 || resposta.status === 403) {
            window.location.assign("/login");
            return;
        }

        if (!resposta.ok) {
            console.error("Resposta da API:", dados);

            const detalhe = Array.isArray(dados?.detail)
                ? dados.detail.map(item => item.msg).join(" | ")
                : dados?.detail || dados?.mensagem;

            throw new Error(
                detalhe || `Falha ao salvar usuário (HTTP ${resposta.status}).`
            );
        }

        elementos.modal?.close();
        elementos.formulario.reset();

        await carregarUsuarios();

    } catch (erro) {
        console.error("Erro ao salvar usuário:", erro);

        mostrarErroFormulario(
            erro.message || "Não foi possível salvar o usuário."
        );
    }
}

function alternarStatusUsuario(id) {
    const usuario = usuarios.find(
        item => String(item.id) === String(id)
    );

    if (!usuario) return;

    fetch(`${API_USUARIOS}/${id}`, {
        method: "PATCH",
        credentials: "same-origin",
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
        body: JSON.stringify({ ativo: !usuario.ativo })
    })
    .then(resposta => {
        if (resposta.status === 401 || resposta.status === 403) {
            window.location.assign("/login");
            return null;
        }

        if (!resposta.ok) {
            throw new Error(`Falha ao alterar status (HTTP ${resposta.status}).`);
        }

        carregarUsuarios();
    })
    .catch(erro => {
        console.error("Erro ao alterar status:", erro);
        alert("Não foi possível alterar o status do usuário.");
    });
}

function abrirNovoUsuario() {
    if (!elementos.formulario || !elementos.modal) return;

    elementos.formulario.reset();
    elementos.id.value = "";
    elementos.tituloModal.textContent = "Novo usuário";
    elementos.senha.required = true;
    elementos.erro.textContent = "";

    elementos.modal.showModal();
}

function abrirEdicao(id) {
    const usuario = usuarios.find(
        item => String(item.id) === String(id)
    );

    if (!usuario) return;

    elementos.formulario.reset();
    elementos.id.value = usuario.id;
    elementos.nome.value = usuario.nome;
    elementos.email.value = usuario.email;
    elementos.perfil.value = usuario.perfil;
    elementos.ativo.value = String(usuario.ativo);

    elementos.tituloModal.textContent = "Editar usuário";
    elementos.senha.required = false;
    elementos.erro.textContent = "";

    elementos.modal.showModal();
}

function mostrarErroFormulario(mensagem) {
    if (elementos.erro) {
        elementos.erro.textContent = mensagem;
    }
}

const botaoNovo = document.getElementById("novoUsuario");
const botaoFechar = document.getElementById("fecharModal");
const botaoCancelar = document.getElementById("cancelarUsuario");

if (botaoNovo) {
    botaoNovo.addEventListener("click", abrirNovoUsuario);
}

if (botaoFechar) {
    botaoFechar.addEventListener("click", () => {
        elementos.modal?.close();
    });
}

if (botaoCancelar) {
    botaoCancelar.addEventListener("click", () => {
        elementos.modal?.close();
    });
}

if (elementos.busca) {
    elementos.busca.addEventListener("input", renderizarUsuarios);
}

if (elementos.filtro) {
    elementos.filtro.addEventListener("change", renderizarUsuarios);
}

if (elementos.lista) {
    elementos.lista.addEventListener("click", evento => {
        const botaoEditar = evento.target.closest("[data-editar]");
        const botaoAlternar = evento.target.closest("[data-alternar]");

        if (botaoEditar) {
            abrirEdicao(botaoEditar.dataset.editar);
            return;
        }

        if (botaoAlternar) {
            alternarStatusUsuario(botaoAlternar.dataset.alternar);
        }
    });
}

if (elementos.formulario) {
    elementos.formulario.addEventListener("submit", salvarUsuario);
}

carregarUsuarios();
