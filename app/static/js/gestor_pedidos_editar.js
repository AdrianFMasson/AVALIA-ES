"use strict";

const pedidoId = document.getElementById("id_pedido").value;
const formulario = document.getElementById("formEditarPedido");
const mensagemTela = document.getElementById("mensagemTela");
const botaoSalvar = document.getElementById("botaoSalvar");
const carregamento = document.getElementById("carregamento");
const campoStatus = document.getElementById("status");

let pedidoOriginal = null;

function mostrarMensagem(texto, tipo = "") {
    mensagemTela.textContent = texto;
    mensagemTela.className = tipo ? `mensagem ${tipo}` : "mensagem";
    mensagemTela.hidden = !texto;
}

function formatarData(valor) {
    if (!valor) return "—";

    const data = new Date(valor);
    return Number.isNaN(data.getTime()) ? valor : data.toLocaleString("pt-BR");
}

function normalizarMensagemErro(detalhe) {
    const mensagem = String(detalhe || "").toLowerCase();

    if (
        mensagem.includes("pedido encerrado não pode ser reaberto") ||
        mensagem.includes("pedido encerrado nao pode ser reaberto") ||
        mensagem.includes("1644")
    ) {
        return "Não foi possível atualizar o pedido. Este pedido já foi encerrado e não pode ser reaberto. A alteração não foi realizada.";
    }

    return "Não foi possível salvar as alterações do pedido. Verifique os dados e tente novamente.";
}

async function carregarPedido() {
    try {
        const resposta = await fetch("/pedido");
        const pedidos = await resposta.json().catch(() => []);

        if (!resposta.ok || !Array.isArray(pedidos)) {
            throw new Error("Não foi possível consultar os pedidos.");
        }

        pedidoOriginal = pedidos.find(
            p => String(p.id_pedido) === String(pedidoId)
        );

        if (!pedidoOriginal) {
            throw new Error("Pedido não encontrado.");
        }

        document.getElementById("id_usuario").value = pedidoOriginal.id_usuario;
        document.getElementById("id_equipamento").value = pedidoOriginal.id_equipamento;
        document.getElementById("discente").value = pedidoOriginal.id_usuario;
        document.getElementById("equipamento").value = pedidoOriginal.id_equipamento;
        document.getElementById("dataPedido").value = formatarData(pedidoOriginal.data_pedido);
        campoStatus.value = pedidoOriginal.status;

        carregamento.hidden = true;
        formulario.hidden = false;
    } catch (erro) {
        carregamento.textContent = erro.message || "Erro ao carregar o pedido.";
        mostrarMensagem(carregamento.textContent, "mensagem-erro");
    }
}

formulario.addEventListener("submit", async evento => {
    evento.preventDefault();

    if (!pedidoOriginal) {
        mostrarMensagem("Não foi possível identificar o pedido.", "mensagem-erro");
        return;
    }

    mostrarMensagem("");
    botaoSalvar.disabled = true;
    botaoSalvar.textContent = "Salvando...";

    const dados = {
        status: campoStatus.value,
        id_usuario: Number(pedidoOriginal.id_usuario),
        id_equipamento: Number(pedidoOriginal.id_equipamento)
    };

    try {
        const resposta = await fetch(`/pedido/${encodeURIComponent(pedidoId)}`, {
            method: "PUT",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(dados)
        });

        const resultado = await resposta.json().catch(() => ({}));

        if (!resposta.ok) {
            mostrarMensagem(normalizarMensagemErro(resultado.detail), "mensagem-erro");
            return;
        }

        mostrarMensagem("Status do pedido atualizado com sucesso.", "mensagem-sucesso");

        setTimeout(() => {
            window.location.href = "/gestor_pedidos";
        }, 1000);
    } catch {
        mostrarMensagem(
            "Não foi possível conectar ao servidor. Verifique sua conexão e tente novamente.",
            "mensagem-erro"
        );
    } finally {
        botaoSalvar.disabled = false;
        botaoSalvar.textContent = "Salvar alterações";
    }
});

carregarPedido();