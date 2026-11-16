"use strict";

// =========================================================
// ELEMENTOS
// =========================================================

const formulario = document.getElementById("formulario-categoria");

const campoId = document.getElementById("id-categoria");
const campoNome = document.getElementById("nome-categoria");
const campoDescricao = document.getElementById("descricao-categoria");

const listaCategorias = document.getElementById("lista-categorias");

const botaoSalvar = document.getElementById("botao-salvar");
const botaoCancelar = document.getElementById("botao-cancelar");
const botaoAtualizar = document.getElementById("botao-atualizar");

const tituloFormulario = document.getElementById("titulo-formulario");

const pesquisaCategoria = document.getElementById("pesquisa-categoria");
const filtroStatus = document.getElementById("filtro-status");

const mensagemCategorias = document.getElementById("mensagem-categorias");

const totalCategorias = document.getElementById("total-categorias");
const categoriasAtivas = document.getElementById("categorias-ativas");
const categoriasInativas = document.getElementById("categorias-inativas");
const categoriasExibidas = document.getElementById("categorias-exibidas");

const contadorListagem = document.getElementById("contador-listagem");


// =========================================================
// ESTADO
// =========================================================

let categorias = [];
let mensagemTimeout = null;


// =========================================================
// CONFIGURAÇÕES
// =========================================================

const API_CATEGORIAS = "/api/admin/categorias";


// =========================================================
// REQUISIÇÕES
// =========================================================

async function requisicaoAPI(url, opcoes = {}) {

    const resposta = await fetch(url, {
        ...opcoes,

        credentials: "same-origin",

        headers: {
            "Content-Type": "application/json",
            ...(opcoes.headers || {})
        }
    });

    let dados = null;

    const tipoConteudo = resposta.headers.get("content-type") || "";

    if (tipoConteudo.includes("application/json")) {
        dados = await resposta.json();
    } else {
        dados = await resposta.text();
    }

    if (!resposta.ok) {

        if (resposta.status === 401) {
            window.location.href = "/login";
            throw new Error("Sua sessão expirou. Faça login novamente.");
        }

        if (resposta.status === 403) {
            throw new Error("Você não tem permissão para realizar esta operação.");
        }

        const detalhe =
            dados && typeof dados === "object"
                ? dados.detail
                : dados;

        throw new Error(
            detalhe || "Não foi possível concluir a operação."
        );
    }

    return dados;
}


// =========================================================
// MENSAGENS
// =========================================================

function mostrarMensagem(texto, tipo = "sucesso") {

    clearTimeout(mensagemTimeout);

    mensagemCategorias.textContent = texto;
    mensagemCategorias.className = `mensagem-sistema ${tipo}`;
    mensagemCategorias.hidden = false;

    mensagemTimeout = setTimeout(() => {
        mensagemCategorias.hidden = true;
    }, 5000);
}


// =========================================================
// FORMATAÇÃO
// =========================================================

function escaparHTML(valor) {

    return String(valor ?? "").replace(/[&<>"']/g, caractere => {

        const entidades = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#039;"
        };

        return entidades[caractere];
    });
}


// =========================================================
// CARREGAMENTO DAS CATEGORIAS
// =========================================================

async function carregarCategorias() {

    listaCategorias.innerHTML = `
        <tr>
            <td colspan="5" class="mensagem-vazia">
                Carregando categorias...
            </td>
        </tr>
    `;

    try {

        const resultado = await requisicaoAPI(API_CATEGORIAS);

        categorias = Array.isArray(resultado) ? resultado : [];

        atualizarIndicadores();
        aplicarFiltros();

    } catch (erro) {

        listaCategorias.innerHTML = `
            <tr>
                <td colspan="5" class="mensagem-vazia">
                    Não foi possível carregar as categorias.
                </td>
            </tr>
        `;

        mostrarMensagem(erro.message, "erro");
    }
}


// =========================================================
// INDICADORES
// =========================================================

function atualizarIndicadores() {

    const total = categorias.length;

    const ativas = categorias.filter(
        categoria => categoria.ativo === true
    ).length;

    const inativas = total - ativas;

    totalCategorias.textContent = total;
    categoriasAtivas.textContent = ativas;
    categoriasInativas.textContent = inativas;
}


// =========================================================
// FILTROS
// =========================================================

function aplicarFiltros() {

    const termo = pesquisaCategoria.value
        .trim()
        .toLocaleLowerCase("pt-BR");

    const statusSelecionado = filtroStatus.value;

    let resultado = [...categorias];

    if (termo) {

        resultado = resultado.filter(categoria => {

            const nome = String(categoria.nome || "")
                .toLocaleLowerCase("pt-BR");

            const descricao = String(categoria.descricao || "")
                .toLocaleLowerCase("pt-BR");

            return nome.includes(termo) || descricao.includes(termo);
        });
    }

    if (statusSelecionado === "ativas") {
        resultado = resultado.filter(categoria => categoria.ativo === true);
    }

    if (statusSelecionado === "inativas") {
        resultado = resultado.filter(categoria => categoria.ativo === false);
    }

    renderizarCategorias(resultado);
}


// =========================================================
// RENDERIZAÇÃO DA TABELA
// =========================================================

function renderizarCategorias(lista) {

    categoriasExibidas.textContent = lista.length;

    contadorListagem.textContent =
        `${lista.length} ${lista.length === 1 ? "categoria encontrada" : "categorias encontradas"}`;

    if (lista.length === 0) {

        listaCategorias.innerHTML = `
            <tr>
                <td colspan="5" class="mensagem-vazia">
                    Nenhuma categoria encontrada.
                </td>
            </tr>
        `;

        return;
    }

    listaCategorias.innerHTML = lista.map(categoria => {

        const id = Number(categoria.id_categoria ?? categoria.id);

        const nome = escaparHTML(categoria.nome);
        const descricao = escaparHTML(categoria.descricao || "Sem descrição");

        const ativo = categoria.ativo === true;

        const situacao = ativo
            ? `<span class="status-categoria ativa">Ativa</span>`
            : `<span class="status-categoria inativa">Inativa</span>`;

        const textoBotao = ativo ? "Desativar" : "Ativar";

        const classeBotao = ativo
            ? "botao-acao desativar"
            : "botao-acao ativar";

        const iconeBotao = ativo ? "⊘" : "✓";

        return `
            <tr>

                <td>#${id}</td>

                <td>
                    <strong class="nome-categoria-tabela">
                        ${nome}
                    </strong>
                </td>

                <td class="descricao-tabela">
                    ${descricao}
                </td>

                <td>
                    ${situacao}
                </td>

                <td>
                    <div class="acoes-tabela">

                        <button
                            type="button"
                            class="botao-acao editar"
                            data-acao="editar"
                            data-id="${id}"
                            title="Editar categoria"
                        >
                            ✎ Editar
                        </button>

                        <button
                            type="button"
                            class="${classeBotao}"
                            data-acao="status"
                            data-id="${id}"
                            data-ativo="${ativo}"
                            title="${textoBotao} categoria"
                        >
                            ${iconeBotao} ${textoBotao}
                        </button>

                    </div>
                </td>

            </tr>
        `;

    }).join("");
}


// =========================================================
// CADASTRAR OU EDITAR CATEGORIA
// =========================================================

formulario.addEventListener("submit", async evento => {

    evento.preventDefault();

    const id = campoId.value.trim();

    const nome = campoNome.value.trim();
    const descricao = campoDescricao.value.trim();

    if (!nome) {
        mostrarMensagem("Informe o nome da categoria.", "erro");
        campoNome.focus();
        return;
    }

    if (nome.length > 100) {
        mostrarMensagem("O nome deve ter no máximo 100 caracteres.", "erro");
        campoNome.focus();
        return;
    }

    if (descricao.length > 255) {
        mostrarMensagem("A descrição deve ter no máximo 255 caracteres.", "erro");
        campoDescricao.focus();
        return;
    }

    const dados = {
        nome: nome,
        descricao: descricao || null
    };

    const editando = Boolean(id);

    const url = editando
        ? `${API_CATEGORIAS}/${encodeURIComponent(id)}`
        : API_CATEGORIAS;

    const metodo = editando ? "PUT" : "POST";

    botaoSalvar.disabled = true;
    botaoSalvar.textContent = editando
        ? "Salvando alterações..."
        : "Cadastrando...";

    try {

        await requisicaoAPI(url, {
            method: metodo,
            body: JSON.stringify(dados)
        });

        mostrarMensagem(
            editando
                ? "Categoria atualizada com sucesso."
                : "Categoria cadastrada com sucesso.",
            "sucesso"
        );

        limparFormulario();

        await carregarCategorias();

    } catch (erro) {

        mostrarMensagem(erro.message, "erro");

    } finally {

        botaoSalvar.disabled = false;

        botaoSalvar.innerHTML = editando
            ? "Salvar alterações"
            : "<span>＋</span> Cadastrar categoria";
    }
});


// =========================================================
// PREPARAR EDIÇÃO
// =========================================================

function editarCategoria(id) {

    const categoria = categorias.find(item =>
        Number(item.id_categoria ?? item.id) === Number(id)
    );

    if (!categoria) {
        mostrarMensagem("Categoria não encontrada.", "erro");
        return;
    }

    campoId.value = categoria.id_categoria ?? categoria.id;
    campoNome.value = categoria.nome || "";
    campoDescricao.value = categoria.descricao || "";

    tituloFormulario.textContent = "Editar categoria";

    botaoSalvar.innerHTML = "Salvar alterações";

    botaoCancelar.hidden = false;

    campoNome.focus();

    document.querySelector(".painel-formulario").scrollIntoView({
        behavior: "smooth",
        block: "start"
    });
}


// =========================================================
// ATIVAR OU DESATIVAR CATEGORIA
// =========================================================

async function alterarStatusCategoria(id, ativoAtual) {

    const novoStatus = !ativoAtual;

    const acao = novoStatus ? "ativar" : "desativar";

    const confirmado = window.confirm(
        `Deseja realmente ${acao} esta categoria?`
    );

    if (!confirmado) {
        return;
    }

    try {

        await requisicaoAPI(
            `${API_CATEGORIAS}/${encodeURIComponent(id)}/status`,
            {
                method: "PATCH",
                body: JSON.stringify({
                    ativo: novoStatus
                })
            }
        );

        mostrarMensagem(
            novoStatus
                ? "Categoria ativada com sucesso."
                : "Categoria desativada com sucesso.",
            "sucesso"
        );

        await carregarCategorias();

    } catch (erro) {

        mostrarMensagem(erro.message, "erro");
    }
}


// =========================================================
// AÇÕES DA TABELA
// =========================================================

listaCategorias.addEventListener("click", evento => {

    const botao = evento.target.closest("button[data-acao]");

    if (!botao) {
        return;
    }

    const acao = botao.dataset.acao;
    const id = botao.dataset.id;

    if (acao === "editar") {
        editarCategoria(id);
        return;
    }

    if (acao === "status") {

        const ativoAtual = botao.dataset.ativo === "true";

        alterarStatusCategoria(id, ativoAtual);
    }
});


// =========================================================
// LIMPAR FORMULÁRIO
// =========================================================

function limparFormulario() {

    formulario.reset();

    campoId.value = "";

    tituloFormulario.textContent = "Nova categoria";

    botaoSalvar.innerHTML = "<span>＋</span> Cadastrar categoria";

    botaoCancelar.hidden = true;
}


// =========================================================
// EVENTOS
// =========================================================

botaoCancelar.addEventListener("click", () => {
    limparFormulario();
});

botaoAtualizar.addEventListener("click", () => {
    carregarCategorias();
});

pesquisaCategoria.addEventListener("input", () => {
    aplicarFiltros();
});

filtroStatus.addEventListener("change", () => {
    aplicarFiltros();
});


// =========================================================
// INICIALIZAÇÃO
// =========================================================

document.addEventListener("DOMContentLoaded", () => {
    carregarCategorias();
});