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


/**
 * Exibe uma mensagem na tela.
 */
function mostrarMensagem(texto, tipo = "") {
    mensagemTela.textContent = texto;
    mensagemTela.className = tipo
        ? `mensagem ${tipo}`
        : "mensagem";
}


/**
 * Escapa valores para evitar a inserção de HTML não confiável.
 */
function escaparHTML(valor) {
    return String(valor ?? "").replace(/[&<>"']/g, caractere => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    })[caractere]);
}


/**
 * Formata o status do usuário.
 */
function formatarStatus(ativo) {
    return ativo
        ? '<span class="status status-ativo">Ativo</span>'
        : '<span class="status status-inativo">Inativo</span>';
}


/**
 * Atualiza o contador de discentes.
 */
function atualizarContador(quantidade) {
    contadorDiscentes.textContent =
        `${quantidade} ${quantidade === 1 ? "discente" : "discentes"}`;
}


/**
 * Realiza requisições autenticadas usando o cookie access_token.
 *
 * O navegador envia automaticamente o cookie nas requisições
 * same-origin, desde que ele esteja configurado corretamente.
 */
async function fetchAutenticado(url, opcoes = {}) {
    const resposta = await fetch(url, {
        ...opcoes,
        credentials: "same-origin"
    });

    if (resposta.status === 401) {
        window.location.href = "/login";

        throw new Error(
            "Sua sessão expirou ou você não está autenticado."
        );
    }

    if (resposta.status === 403) {
        throw new Error(
            "Seu perfil não tem permissão para acessar este recurso."
        );
    }

    if (!resposta.ok) {
        throw new Error(
            `Não foi possível concluir a requisição. HTTP ${resposta.status}.`
        );
    }

    return resposta;
}


/**
 * Renderiza a tabela de discentes.
 */
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
                <button
                    type="button"
                    class="botao botao-editar"
                    data-id="${escaparHTML(usuario.id_usuario)}"
                >
                    Editar
                </button>
            </td>
        `;

        tabelaDiscentes.appendChild(linha);
    });
}


/**
 * Consulta os perfis disponíveis e identifica o perfil DISCENTE.
 */
async function carregarPerfis() {
    const resposta = await fetchAutenticado(API_PERFIS);
    const perfis = await resposta.json();

    if (!Array.isArray(perfis)) {
        throw new Error(
            "A resposta da API de perfis não contém uma lista válida."
        );
    }

    const perfilDiscente = perfis.find(perfil =>
        String(perfil.perfil).toUpperCase() === "DISCENTE"
    );

    if (!perfilDiscente) {
        throw new Error(
            "O perfil DISCENTE não foi encontrado na API."
        );
    }

    idPerfilDiscente = perfilDiscente.id_perfil;
}


/**
 * Consulta os usuários autorizados e filtra os discentes.
 */
async function carregarDiscentes() {
    tabelaDiscentes.innerHTML = `
        <tr>
            <td colspan="6" class="estado-tabela">
                Carregando discentes...
            </td>
        </tr>
    `;

    mostrarMensagem("");

    try {
        const resposta = await fetchAutenticado(API_USUARIOS);
        const usuarios = await resposta.json();

        if (!Array.isArray(usuarios)) {
            throw new Error(
                "A resposta da API não contém uma lista válida de usuários."
            );
        }

        if (idPerfilDiscente === null) {
            await carregarPerfis();
        }

        discentes = usuarios.filter(usuario =>
            Number(usuario.id_perfil) === Number(idPerfilDiscente)
        );

        aplicarFiltros();

    } catch (erro) {
        console.error("Erro ao carregar discentes:", erro);

        tabelaDiscentes.replaceChildren();

        const linha = document.createElement("tr");
        const celula = document.createElement("td");

        celula.colSpan = 6;
        celula.className = "estado-tabela";
        celula.textContent = "Não foi possível carregar os discentes.";

        linha.appendChild(celula);
        tabelaDiscentes.appendChild(linha);

        atualizarContador(0);

        if (erro instanceof Error) {
            mostrarMensagem(erro.message, "mensagem-erro");
        } else {
            mostrarMensagem(
                "Ocorreu um erro inesperado.",
                "mensagem-erro"
            );
        }
    }
}


/**
 * Aplica os filtros de ID e status.
 */
function aplicarFiltros() {
    const idInformado = pesquisaId.value.trim();
    const statusInformado = filtroStatus.value;

    const resultado = discentes.filter(usuario => {
        const correspondeId =
            !idInformado ||
            String(usuario.id_usuario) === idInformado;

        const correspondeStatus =
            statusInformado === "" ||
            String(Boolean(usuario.ativo)) === statusInformado;

        return correspondeId && correspondeStatus;
    });

    renderizarTabela(resultado);
}


/**
 * Trata a pesquisa.
 */
formPesquisa.addEventListener("submit", evento => {
    evento.preventDefault();
    aplicarFiltros();
});


/**
 * Limpa os filtros e as mensagens.
 */
document.getElementById("limparPesquisa").addEventListener("click", () => {
    formPesquisa.reset();

    aplicarFiltros();
    mostrarMensagem("");
});


/**
 * Abre a página de edição do discente selecionado.
 */
tabelaDiscentes.addEventListener("click", evento => {
    const botao = evento.target.closest("[data-id]");

    if (!botao) {
        return;
    }

    const usuarioId = botao.dataset.id;

    window.location.href =
        `/gestor/usuarios/editar/${encodeURIComponent(usuarioId)}`;
});


/**
 * Inicializa a página.
 */
carregarDiscentes();