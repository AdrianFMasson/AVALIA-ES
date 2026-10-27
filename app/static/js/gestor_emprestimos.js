/* =========================================================
   THE IRON COMPASS — GESTOR DE EMPRÉSTIMOS
   ========================================================= */

"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const API_PEDIDOS = "/api/gestor/emprestimos";

    /*
     * IMPORTANTE:
     * Estes valores precisam corresponder exatamente aos valores
     * definidos no enum de status do seu backend.
     */
    const STATUS = {
        pendente: "PENDENTE",
        aprovado: "APROVADO",
        negado: "NEGADO"
    };

    const elementos = {
        lista: document.getElementById("lista-solicitacoes"),
        busca: document.getElementById("busca"),
        filtroStatus: document.getElementById("filtro-status"),
        mensagem: document.getElementById("mensagem"),
        contador: document.getElementById("contador-resultados"),

        total: document.getElementById("total-solicitacoes"),
        pendentes: document.getElementById("total-pendentes"),
        aprovados: document.getElementById("total-aprovados"),
        negados: document.getElementById("total-negados"),

        atualizar: document.getElementById("botao-atualizar"),

        modal: document.getElementById("modal-confirmacao"),
        tituloModal: document.getElementById("titulo-modal"),
        textoModal: document.getElementById("texto-modal"),
        iconeModal: document.getElementById("icone-modal"),
        cancelar: document.getElementById("cancelar-acao"),
        confirmar: document.getElementById("confirmar-acao")
    };

    let solicitacoes = [];
    let acaoPendente = null;
    let carregando = false;
    let salvando = false;

    /* =====================================================
       UTILITÁRIOS
       ===================================================== */

    function normalizar(valor) {
        return String(valor ?? "")
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "")
            .toLocaleLowerCase("pt-BR")
            .trim();
    }

    function escaparHTML(valor) {
        return String(valor ?? "").replace(/[&<>"']/g, caractere => {
            const mapa = {
                "&": "&amp;",
                "<": "&lt;",
                ">": "&gt;",
                '"': "&quot;",
                "'": "&#39;"
            };

            return mapa[caractere];
        });
    }

    function formatarData(valor) {
        if (!valor) {
            return "Não informada";
        }

        const data = new Date(valor);

        if (Number.isNaN(data.getTime())) {
            return "Data indisponível";
        }

        return new Intl.DateTimeFormat("pt-BR", {
            dateStyle: "short",
            timeStyle: "short"
        }).format(data);
    }

    function obterStatusOriginal(valor) {
        return String(valor ?? "")
            .trim()
            .toUpperCase()
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "");
    }

    function obterCategoriaStatus(valor) {
        const status = obterStatusOriginal(valor);

        if (
            status === STATUS.aprovado ||
            status === "APROVADA" ||
            status === "APPROVED"
        ) {
            return "aprovado";
        }

        if (
            status === STATUS.negado ||
            status === "NEGADA" ||
            status === "RECUSADO" ||
            status === "RECUSADA" ||
            status === "REJEITADO" ||
            status === "REJEITADA" ||
            status === "REJECTED"
        ) {
            return "negado";
        }

        if (
            status === "EMPRESTADO" ||
            status === "EM_ANDAMENTO" ||
            status === "DEVOLVIDO" ||
            status === "CONCLUIDO" ||
            status === "CONCLUÍDO"
        ) {
            return "finalizado";
        }

        return "pendente";
    }

    function obterTextoStatus(valor) {
        const categoria = obterCategoriaStatus(valor);

        if (categoria === "aprovado") {
            return "Aprovado";
        }

        if (categoria === "negado") {
            return "Negado";
        }

        if (categoria === "finalizado") {
            return String(valor).replaceAll("_", " ");
        }

        return "Pendente";
    }

    function mostrarMensagem(texto, tipo = "info") {
        elementos.mensagem.textContent = texto;
        elementos.mensagem.className = `mensagem ${tipo}`;
        elementos.mensagem.hidden = false;
    }

    function esconderMensagem() {
        elementos.mensagem.hidden = true;
        elementos.mensagem.textContent = "";
        elementos.mensagem.className = "mensagem";
    }

    function definirCarregamento(ativo) {
        carregando = ativo;
        elementos.atualizar.disabled = ativo || salvando;

        if (ativo) {
            elementos.atualizar.textContent = "Carregando...";
        } else {
            elementos.atualizar.textContent = "↻ Atualizar";
        }
    }

    /* =====================================================
       REQUISIÇÕES À API
       ===================================================== */

    async function requisicao(url, opcoes = {}) {
        const resposta = await fetch(url, {
            credentials: "same-origin",
            ...opcoes,
            headers: {
                Accept: "application/json",
                ...(opcoes.body
                    ? { "Content-Type": "application/json" }
                    : {}),
                ...opcoes.headers
            }
        });

        if (resposta.status === 401 || resposta.status === 403) {
            throw new Error(
                "Sua sessão expirou ou você não tem permissão para executar esta ação."
            );
        }

        if (!resposta.ok) {
            let detalhe = "";

            try {
                const dados = await resposta.json();
                detalhe = dados.detail || dados.mensagem || "";
            } catch {
                detalhe = "";
            }

            throw new Error(
                detalhe || `A solicitação falhou (HTTP ${resposta.status}).`
            );
        }

        if (resposta.status === 204) {
            return null;
        }

        return resposta.json();
    }

    async function carregarSolicitacoes() {
        if (carregando || salvando) {
            return;
        }

        esconderMensagem();
        definirCarregamento(true);

        elementos.lista.innerHTML = `
            <tr>
                <td colspan="6" class="estado-tabela">
                    Carregando solicitações...
                </td>
            </tr>
        `;

        try {
            const dados = await requisicao(API_PEDIDOS);

            if (!Array.isArray(dados)) {
                throw new Error(
                    "A API retornou um formato inesperado. Era esperada uma lista."
                );
            }

            solicitacoes = dados;
            atualizarIndicadores();
            renderizarSolicitacoes();

        } catch (erro) {
            elementos.lista.innerHTML = `
                <tr>
                    <td colspan="6" class="estado-tabela">
                        Não foi possível carregar as solicitações.<br>
                        ${escaparHTML(erro.message)}
                    </td>
                </tr>
            `;

            mostrarMensagem(erro.message, "erro");
            elementos.contador.textContent = "Falha ao carregar registros.";

        } finally {
            definirCarregamento(false);
        }
    }

    async function atualizarStatus(idPedido, novoStatus) {
        if (salvando) {
            return;
        }

        salvando = true;
        elementos.confirmar.disabled = true;
        elementos.cancelar.disabled = true;
        elementos.confirmar.textContent = "Salvando...";

        try {
            const resultado = await requisicao(
                `${API_PEDIDOS}/${encodeURIComponent(idPedido)}`,
                {
                    method: "PATCH",
                    body: JSON.stringify({
                        status: novoStatus
                    })
                }
            );

            fecharModal();

            mostrarMensagem(
                resultado?.mensagem ||
                    "Status atualizado com sucesso.",
                "sucesso"
            );

            /*
             * Busca novamente os dados do servidor para garantir
             * que a interface reflita o estado persistido.
             */
            await carregarSolicitacoes();

        } catch (erro) {
            fecharModal();
            mostrarMensagem(
                `Não foi possível atualizar o pedido: ${erro.message}`,
                "erro"
            );

        } finally {
            salvando = false;
            elementos.confirmar.disabled = false;
            elementos.cancelar.disabled = false;
            elementos.confirmar.textContent = "Confirmar";
            elementos.atualizar.disabled = carregando;
        }
    }

    /* =====================================================
       INDICADORES
       ===================================================== */

    function atualizarIndicadores() {
        const pendentes = solicitacoes.filter(
            pedido => obterCategoriaStatus(pedido.status) === "pendente"
        ).length;

        const aprovados = solicitacoes.filter(
            pedido => obterCategoriaStatus(pedido.status) === "aprovado"
        ).length;

        const negados = solicitacoes.filter(
            pedido => obterCategoriaStatus(pedido.status) === "negado"
        ).length;

        elementos.total.textContent = solicitacoes.length;
        elementos.pendentes.textContent = pendentes;
        elementos.aprovados.textContent = aprovados;
        elementos.negados.textContent = negados;
    }

    /* =====================================================
       FILTROS
       ===================================================== */

    function obterSolicitacoesFiltradas() {
        const termo = normalizar(elementos.busca.value);
        const filtroStatus = elementos.filtroStatus.value;

        return solicitacoes.filter(pedido => {
            const categoria = obterCategoriaStatus(pedido.status);

            const textoPesquisa = normalizar([
                pedido.id,
                pedido.id_pedido,
                pedido.id_usuario,
                pedido.usuario,
                pedido.id_equipamento,
                pedido.equipamento,
                pedido.status
            ].join(" "));

            const correspondeBusca =
                !termo || textoPesquisa.includes(termo);

            const correspondeStatus =
                filtroStatus === "TODOS" ||
                (
                    filtroStatus === STATUS.pendente &&
                    categoria === "pendente"
                ) ||
                (
                    filtroStatus === STATUS.aprovado &&
                    categoria === "aprovado"
                ) ||
                (
                    filtroStatus === STATUS.negado &&
                    categoria === "negado"
                );

            return correspondeBusca && correspondeStatus;
        });
    }

    /* =====================================================
       RENDERIZAÇÃO
       ===================================================== */

    function criarLinha(pedido) {
        const id = pedido.id_pedido ?? pedido.id;
        const categoria = obterCategoriaStatus(pedido.status);
        const textoStatus = obterTextoStatus(pedido.status);

        const podeDecidir = categoria === "pendente";

        const botoes = podeDecidir
            ? `
                <div class="acoes-linha">
                    <button
                        type="button"
                        class="botao-aprovar"
                        data-acao="aprovar"
                        data-id="${escaparHTML(id)}"
                        aria-label="Aprovar solicitação ${escaparHTML(id)}"
                    >
                        ✓ Aprovar
                    </button>

                    <button
                        type="button"
                        class="botao-negar"
                        data-acao="negar"
                        data-id="${escaparHTML(id)}"
                        aria-label="Negar solicitação ${escaparHTML(id)}"
                    >
                        × Negar
                    </button>
                </div>
            `
            : `
                <span class="texto-auxiliar">
                    ${categoria === "finalizado"
                        ? "Pedido finalizado"
                        : "Decisão registrada"}
                </span>
            `;

        return `
            <tr>
                <td>
                    <span class="codigo-pedido">
                        #${escaparHTML(id ?? "—")}
                    </span>
                </td>

                <td>
                    <span class="nome-principal">
                        ${escaparHTML(pedido.usuario || "Usuário não informado")}
                    </span>
                    <span class="texto-auxiliar">
                        ID: ${escaparHTML(pedido.id_usuario ?? "—")}
                    </span>
                </td>

                <td>
                    <span class="nome-principal">
                        ${escaparHTML(pedido.equipamento || "Equipamento não informado")}
                    </span>
                    <span class="texto-auxiliar">
                        ID: ${escaparHTML(pedido.id_equipamento ?? "—")}
                    </span>
                </td>

                <td>
                    <span class="data-pedido">
                        ${escaparHTML(formatarData(pedido.data_pedido))}
                    </span>
                </td>

                <td>
                    <span class="status ${categoria}">
                        ${escaparHTML(textoStatus)}
                    </span>
                </td>

                <td>${botoes}</td>
            </tr>
        `;
    }

    function renderizarSolicitacoes() {
        const filtradas = obterSolicitacoesFiltradas();

        if (filtradas.length === 0) {
            elementos.lista.innerHTML = `
                <tr>
                    <td colspan="6" class="estado-tabela">
                        Nenhuma solicitação encontrada para os filtros selecionados.
                    </td>
                </tr>
            `;

            elementos.contador.textContent = "Nenhum registro encontrado.";
            return;
        }

        elementos.lista.innerHTML = filtradas
            .map(criarLinha)
            .join("");

        elementos.contador.textContent =
            `Exibindo ${filtradas.length} de ${solicitacoes.length} solicitação(ões).`;
    }

    /* =====================================================
       MODAL DE CONFIRMAÇÃO
       ===================================================== */

    function abrirModal(pedido, decisao) {
        if (salvando) {
            return;
        }

        const id = pedido.id_pedido ?? pedido.id;

        if (decisao === "aprovar") {
            acaoPendente = {
                id,
                status: STATUS.aprovado
            };

            elementos.tituloModal.textContent = "Aprovar solicitação?";
            elementos.textoModal.textContent =
                `Deseja aprovar o empréstimo do equipamento "${pedido.equipamento}" para ${pedido.usuario}?`;
            elementos.iconeModal.textContent = "✓";

            elementos.confirmar.style.background = "var(--sucesso)";
            elementos.confirmar.style.borderColor = "var(--sucesso)";

        } else {
            acaoPendente = {
                id,
                status: STATUS.negado
            };

            elementos.tituloModal.textContent = "Negar solicitação?";
            elementos.textoModal.textContent =
                `Deseja negar a solicitação de "${pedido.equipamento}" feita por ${pedido.usuario}?`;
            elementos.iconeModal.textContent = "×";

            elementos.confirmar.style.background = "var(--erro)";
            elementos.confirmar.style.borderColor = "var(--erro)";
        }

        elementos.confirmar.textContent = "Confirmar";
        elementos.modal.hidden = false;
        elementos.modal.setAttribute("aria-hidden", "false");
        elementos.cancelar.focus();
    }

    function fecharModal() {
        elementos.modal.hidden = true;
        elementos.modal.setAttribute("aria-hidden", "true");
        acaoPendente = null;
    }

    /* =====================================================
       EVENTOS
       ===================================================== */

    elementos.lista.addEventListener("click", evento => {
        const botao = evento.target.closest("button[data-acao]");

        if (!botao || salvando) {
            return;
        }

        const id = botao.dataset.id;
        const decisao = botao.dataset.acao;

        const pedido = solicitacoes.find(item =>
            String(item.id_pedido ?? item.id) === String(id)
        );

        if (!pedido) {
            mostrarMensagem(
                "Não foi possível localizar essa solicitação. Atualize a lista.",
                "erro"
            );
            return;
        }

        if (obterCategoriaStatus(pedido.status) !== "pendente") {
            mostrarMensagem(
                "Esta solicitação já foi analisada.",
                "info"
            );
            return;
        }

        abrirModal(pedido, decisao);
    });

    elementos.confirmar.addEventListener("click", async () => {
        if (!acaoPendente || salvando) {
            return;
        }

        const acao = { ...acaoPendente };
        await atualizarStatus(acao.id, acao.status);
    });

    elementos.cancelar.addEventListener("click", fecharModal);

    elementos.modal.addEventListener("click", evento => {
        if (evento.target === elementos.modal && !salvando) {
            fecharModal();
        }
    });

    document.addEventListener("keydown", evento => {
        if (
            evento.key === "Escape" &&
            !elementos.modal.hidden &&
            !salvando
        ) {
            fecharModal();
        }
    });

    elementos.busca.addEventListener("input", renderizarSolicitacoes);
    elementos.filtroStatus.addEventListener("change", renderizarSolicitacoes);

    elementos.atualizar.addEventListener("click", carregarSolicitacoes);

    /* =====================================================
       INICIALIZAÇÃO
       ===================================================== */

    carregarSolicitacoes();
});