"use strict";

const API_USUARIOS = "/usuarios";
const API_PERFIS = "/perfil";
const tabelaDiscentes = document.getElementById("tabelaDiscentes");
const mensagemTela = document.getElementById("mensagemTela");
const contadorDiscentes = document.getElementById("contadorDiscentes");
const formPesquisa = document.getElementById("formPesquisa");
const pesquisaId = document.getElementById("pesquisaId");
const filtroStatus = document.getElementById("filtroStatus");
let discentes = [];
let idPerfilDiscente = null;

function mostrarMensagem(texto, tipo = "") {
    mensagemTela.textContent = texto;
    mensagemTela.className = tipo ? `mensagem ${tipo}` : "mensagem";
}

function escaparHTML(valor) {
    return String(valor ?? "").replace(/[&<>"']/g, caractere => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    })[caractere]);
}

function formatarStatus(ativo) {
    return ativo
        ? '<span class="status status-ativo">Ativo</span>'
        : '<span class="status status-inativo">Inativo</span>';
}

function atualizarContador(quantidade) {
    contadorDiscentes.textContent = `${quantidade} ${quantidade === 1 ? "discente" : "discentes"}`;
}

function renderizarTabela(lista) {
    tabelaDiscentes.replaceChildren();
    atualizarContador(lista.length);

    if (!lista.length) {
        const linha = document.createElement("tr");
        const celula = document.createElement("td");
        celula.colSpan = 6;
        celula.className = "estado-tabela";
        celula.textContent = "Nenhum discente encontrado.";
        linha.appendChild(celula);
        tabelaDiscentes.appendChild(linha);
        return;
    }

    lista.forEach(usuario => {
        const linha = document.createElement("tr");
        linha.innerHTML = `
            <td>${escaparHTML(usuario.id_usuario)}</td>
            <td>${escaparHTML(usuario.nome)}</td>
            <td>${escaparHTML(usuario.email)}</td>
            <td>DISCENTE</td>
            <td>${formatarStatus(usuario.ativo)}</td>
            <td>
                <button type="button" class="botao botao-editar" data-id="${escaparHTML(usuario.id_usuario)}">
                    Editar
                </button>
            </td>
        `;
        tabelaDiscentes.appendChild(linha);
    });
}

async function carregarPerfis() {
    try {
        const resposta = await fetch(API_PERFIS);

        if (!resposta.ok) {
            throw new Error("Não foi possível consultar os perfis.");
        }

        const perfis = await resposta.json();
        const perfilDiscente = perfis.find(perfil =>
            String(perfil.perfil).toUpperCase() === "DISCENTE"
        );

        if (perfilDiscente) {
            idPerfilDiscente = perfilDiscente.id_perfil;
        }
    } catch (erro) {
        console.warn("Não foi possível consultar os perfis pela rota /perfil.", erro);
    }
}

async function carregarDiscentes() {
    tabelaDiscentes.innerHTML = `
        <tr><td colspan="6" class="estado-tabela">Carregando discentes...</td></tr>
    `;
    mostrarMensagem("");

    try {
        const resposta = await fetch(API_USUARIOS);

        if (!resposta.ok) {
            throw new Error("Não foi possível carregar os usuários.");
        }

        const usuarios = await resposta.json();

        if (!Array.isArray(usuarios)) {
            throw new Error("A resposta da API não contém uma lista válida de usuários.");
        }

        if (idPerfilDiscente === null) {
            await carregarPerfis();
        }

        if (idPerfilDiscente === null) {
            throw new Error("Não foi possível identificar o ID do perfil DISCENTE. Verifique se existe uma rota GET /perfil.");
        }

        discentes = usuarios.filter(usuario =>
            Number(usuario.id_perfil) === Number(idPerfilDiscente)
        );

        aplicarFiltros();
    } catch (erro) {
        console.error(erro);
        tabelaDiscentes.innerHTML = `
            <tr><td colspan="6" class="estado-tabela">Não foi possível carregar os discentes. Verifique a conexão com o servidor e as rotas da API.</td></tr>
        `;
        atualizarContador(0);
        mostrarMensagem(erro.message, "mensagem-erro");
    }
}

function aplicarFiltros() {
    const idInformado = pesquisaId.value.trim();
    const statusInformado = filtroStatus.value;

    const resultado = discentes.filter(usuario => {
        const correspondeId = !idInformado ||
            String(usuario.id_usuario) === idInformado;

        const correspondeStatus = statusInformado === "" ||
            String(Boolean(usuario.ativo)) === statusInformado;

        return correspondeId && correspondeStatus;
    });

    renderizarTabela(resultado);
}

formPesquisa.addEventListener("submit", evento => {
    evento.preventDefault();
    aplicarFiltros();
});

document.getElementById("limparPesquisa").addEventListener("click", () => {
    formPesquisa.reset();
    aplicarFiltros();
    mostrarMensagem("");
});

tabelaDiscentes.addEventListener("click", evento => {
    const botao = evento.target.closest("[data-id]");

    if (!botao) {
        return;
    }

    const usuarioId = botao.dataset.id;
    window.location.href = `/gestor/usuarios/editar/${encodeURIComponent(usuarioId)}`;
});

carregarDiscentes();