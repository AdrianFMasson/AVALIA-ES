"use strict";

const listaPedidos = document.getElementById("listaPedidos");
const mensagemTela = document.getElementById("mensagemTela");
const busca = document.getElementById("busca");
const filtroStatus = document.getElementById("filtroStatus");
const quantidadeExibida = document.getElementById("quantidadeExibida");
let pedidos = [];

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
        "'": "&#039;"
    })[caractere]);
}

function nomeStatus(status) {
    return ({
        ABERTO: "Aberto",
        EM_ANALISE: "Em análise",
        ENCERRADO: "Encerrado"
    })[status] || status || "Não informado";
}

function formatarData(valor) {
    if (!valor) return "—";
    const data = new Date(valor);
    return Number.isNaN(data.getTime()) ? escaparHTML(valor) : data.toLocaleString("pt-BR");
}

function atualizarResumo() {
    document.getElementById("totalPedidos").textContent = pedidos.length;
    document.getElementById("totalAbertos").textContent = pedidos.filter(p => p.status === "ABERTO").length;
    document.getElementById("totalAnalise").textContent = pedidos.filter(p => p.status === "EM_ANALISE").length;
    document.getElementById("totalEncerrados").textContent = pedidos.filter(p => p.status === "ENCERRADO").length;
}

function renderizarPedidos() {
    const termo = busca.value.trim();
    const status = filtroStatus.value;
    const filtrados = pedidos.filter(p => {
        const correspondeId = !termo || String(p.id_pedido).includes(termo);
        const correspondeStatus = !status || p.status === status;
        return correspondeId && correspondeStatus;
    });

    if (!filtrados.length) {
        listaPedidos.innerHTML = '<tr><td colspan="6" class="vazio">Nenhum pedido encontrado.</td></tr>';
        quantidadeExibida.textContent = "Nenhum registro para exibir.";
        return;
    }

    listaPedidos.innerHTML = filtrados.map(p => `
        <tr>
            <td>#${escaparHTML(p.id_pedido)}</td>
            <td>${escaparHTML(p.id_usuario)}</td>
            <td>${escaparHTML(p.id_equipamento)}</td>
            <td>${formatarData(p.data_pedido)}</td>
            <td><span class="etiqueta-status status-${escaparHTML(p.status)}">${escaparHTML(nomeStatus(p.status))}</span></td>
            <td><a class="botao botao-secundario" href="/gestor/pedidos/editar/${encodeURIComponent(p.id_pedido)}">Editar</a></td>
        </tr>
    `).join("");

    quantidadeExibida.textContent = `Exibindo ${filtrados.length} de ${pedidos.length} pedidos.`;
}

async function carregarPedidos() {
    listaPedidos.innerHTML = '<tr><td colspan="6" class="vazio">Carregando pedidos...</td></tr>';
    mostrarMensagem("");

    try {
        const resposta = await fetch("/pedido");
        const resultado = await resposta.json().catch(() => []);

        if (!resposta.ok) {
            throw new Error(typeof resultado.detail === "string" ? resultado.detail : "Não foi possível carregar os pedidos.");
        }

        if (!Array.isArray(resultado)) {
            throw new Error("A API não retornou uma lista válida de pedidos.");
        }

        pedidos = resultado;
        atualizarResumo();
        renderizarPedidos();
    } catch (erro) {
        listaPedidos.innerHTML = '<tr><td colspan="6" class="vazio">Erro ao carregar os pedidos.</td></tr>';
        quantidadeExibida.textContent = "";
        mostrarMensagem(erro.message || "Erro de conexão com o servidor.", "mensagem-erro");
    }
}

busca.addEventListener("input", renderizarPedidos);
filtroStatus.addEventListener("change", renderizarPedidos);
document.getElementById("botaoAtualizar").addEventListener("click", carregarPedidos);
carregarPedidos();