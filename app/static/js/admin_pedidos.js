"use strict";

const API_PEDIDOS = "/api/admin/pedidos";

const el = {
    lista: document.getElementById("listaPedidos"),
    busca: document.getElementById("buscaPedidos"),
    filtro: document.getElementById("filtroStatus"),
    mensagem: document.getElementById("mensagemPedidos"),

    total: document.getElementById("totalPedidos"),
    abertos: document.getElementById("pedidosAbertos"),
    analise: document.getElementById("pedidosEmAnalise"),
    encerrados: document.getElementById("pedidosEncerrados"),

    atualizar: document.getElementById("atualizarPedidos"),
    modal: document.getElementById("modalStatusPedido"),
    formulario: document.getElementById("formStatusPedido"),
    id: document.getElementById("pedidoId"),
    resumo: document.getElementById("resumoPedido"),
    novoStatus: document.getElementById("novoStatusPedido"),
    erro: document.getElementById("erroPedido")
};

let pedidos = [];
let carregando = false;
let salvando = false;

const STATUS = {
    ABERTO: "Aberto",
    EM_ANALISE: "Em análise",
    ENCERRADO: "Encerrado"
};

function escapar(valor) {
    return String(valor ?? "").replace(/[&<>"']/g, caractere => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    })[caractere]);
}

function formatarData(valor) {
    if (!valor) return "—";

    const data = new Date(valor);

    if (Number.isNaN(data.getTime())) {
        return "—";
    }

    return data.toLocaleString("pt-BR");
}

function nomeStatus(status) {
    return STATUS[status] || status || "Não informado";
}

function normalizarPedido(item) {
    return {
        id: item.id_pedido ?? item.id,
        id_usuario: item.id_usuario,
        usuario: item.usuario ?? item.nome_usuario ?? "Usuário não informado",
        id_equipamento: item.id_equipamento,
        equipamento: item.equipamento ?? item.nome_equipamento ?? "Equipamento não informado",
        data_pedido: item.data_pedido,
        status: item.status
    };
}

function atualizarIndicadores() {
    if (el.total) {
        el.total.textContent = pedidos.length;
    }

    if (el.abertos) {
        el.abertos.textContent =
            pedidos.filter(p => p.status === "ABERTO").length;
    }

    if (el.analise) {
        el.analise.textContent =
            pedidos.filter(p => p.status === "EM_ANALISE").length;
    }

    if (el.encerrados) {
        el.encerrados.textContent =
            pedidos.filter(p => p.status === "ENCERRADO").length;
    }
}

function renderizar() {
    if (!el.lista) return;

    const termo = (el.busca?.value || "")
        .trim()
        .toLocaleLowerCase("pt-BR");

    const filtro = el.filtro?.value || "";

    const filtrados = pedidos.filter(pedido => {
        const texto = [
            pedido.id,
            pedido.usuario,
            pedido.equipamento,
            pedido.id_usuario,
            pedido.id_equipamento
        ].join(" ").toLocaleLowerCase("pt-BR");

        return texto.includes(termo) &&
            (!filtro || pedido.status === filtro);
    });

    el.lista.innerHTML = filtrados.map(pedido => `
        <tr>
            <td>#${escapar(pedido.id)}</td>
            <td>${escapar(pedido.usuario)}</td>
            <td>${escapar(pedido.equipamento)}</td>
            <td>${escapar(formatarData(pedido.data_pedido))}</td>
            <td>
                <span class="status ${escapar(pedido.status.toLowerCase())}">
                    ${escapar(nomeStatus(pedido.status))}
                </span>
            </td>
            <td>
                <button
                    type="button"
                    class="acao"
                    data-editar="${escapar(pedido.id)}"
                >
                    Alterar status
                </button>
            </td>
        </tr>
    `).join("");

    if (el.mensagem && !carregando) {
        el.mensagem.textContent = filtrados.length
            ? ""
            : "Nenhum pedido encontrado.";
    }

    atualizarIndicadores();
}

async function carregarPedidos() {
    if (carregando) return;

    carregando = true;

    if (el.mensagem) {
        el.mensagem.textContent = "Carregando pedidos...";
    }

    try {
        const resposta = await fetch(API_PEDIDOS, {
            method: "GET",
            credentials: "same-origin",
            headers: {
                "Accept": "application/json"
            }
        });

        if (resposta.status === 401) {
            window.location.href = "/login";
            return;
        }

        if (resposta.status === 403) {
            throw new Error("Seu perfil não tem permissão para consultar pedidos.");
        }

        if (!resposta.ok) {
            throw new Error(`Erro ao carregar pedidos (HTTP ${resposta.status}).`);
        }

        const dados = await resposta.json();

        if (!Array.isArray(dados)) {
            throw new Error("A API retornou um formato inválido.");
        }

        pedidos = dados.map(normalizarPedido);
        renderizar();
    } catch (erro) {
        console.error("Erro ao carregar pedidos:", erro);

        if (el.mensagem) {
            el.mensagem.textContent =
                erro.message || "Não foi possível carregar os pedidos.";
        }
    } finally {
        carregando = false;
    }
}

function abrirEdicao(id) {
    const pedido = pedidos.find(item => String(item.id) === String(id));

    if (!pedido || !el.modal) return;

    el.id.value = pedido.id;
    el.novoStatus.value = pedido.status;

    if (el.resumo) {
        el.resumo.textContent =
            `Pedido #${pedido.id} — ${pedido.usuario} — ${pedido.equipamento}`;
    }

    if (el.erro) {
        el.erro.textContent = "";
    }

    el.modal.showModal();
}

async function salvarStatus(evento) {
    evento.preventDefault();

    if (salvando) return;

    const id = el.id.value;
    const status = el.novoStatus.value;

    if (!id || !STATUS[status]) {
        el.erro.textContent = "Selecione um pedido e um status válido.";
        return;
    }

    salvando = true;
    el.erro.textContent = "";

    const botao = el.formulario.querySelector('[type="submit"]');
    if (botao) botao.disabled = true;

    try {
        const resposta = await fetch(`${API_PEDIDOS}/${encodeURIComponent(id)}`, {
            method: "PATCH",
            credentials: "same-origin",
            headers: {
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            body: JSON.stringify({ status })
        });

        if (resposta.status === 401) {
            window.location.href = "/login";
            return;
        }

        const resultado = await resposta.json().catch(() => ({}));

        if (!resposta.ok) {
            throw new Error(
                resultado.detail || `Não foi possível atualizar o pedido (HTTP ${resposta.status}).`
            );
        }

        el.modal.close();
        await carregarPedidos();
    } catch (erro) {
        console.error("Erro ao atualizar pedido:", erro);
        el.erro.textContent = erro.message || "Falha ao salvar o status.";
    } finally {
        salvando = false;
        if (botao) botao.disabled = false;
    }
}

function configurarEventos() {
    el.busca?.addEventListener("input", renderizar);
    el.filtro?.addEventListener("change", renderizar);

    el.atualizar?.addEventListener("click", carregarPedidos);

    el.lista?.addEventListener("click", evento => {
        const botao = evento.target.closest("[data-editar]");
        if (botao) abrirEdicao(botao.dataset.editar);
    });

    document.getElementById("fecharModalPedido")
        ?.addEventListener("click", () => el.modal.close());

    document.getElementById("cancelarStatusPedido")
        ?.addEventListener("click", () => el.modal.close());

    el.formulario?.addEventListener("submit", salvarStatus);
}

configurarEventos();
carregarPedidos();