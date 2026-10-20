"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const API_EQUIPAMENTOS = "/api/admin/equipamentos";

    const el = {
        lista: document.getElementById("listaEquipamentos"),
        busca: document.getElementById("buscaEquipamentos"),
        filtro: document.getElementById("filtroDisponibilidade"),
        mensagem: document.getElementById("mensagemEquipamentos"),

        modal: document.getElementById("modalEquipamento"),
        formulario: document.getElementById("formEquipamento"),
        tituloModal: document.getElementById("tituloModalEquipamento"),
        mensagemFormulario: document.getElementById("mensagemFormulario"),

        id: document.getElementById("equipamentoId"),
        nome: document.getElementById("nomeEquipamento"),
        estoque: document.getElementById("patrimonioEquipamento"),
        categoria: document.getElementById("categoriaEquipamento"),
        descricao: document.getElementById("conservacaoEquipamento"),
        status: document.getElementById("disponibilidadeEquipamento"),

        botaoNovo: document.getElementById("novoEquipamento"),
        botaoSalvar: document.getElementById("salvarEquipamento"),
        botaoFechar: document.getElementById("fecharModal"),
        botaoCancelar: document.getElementById("cancelarEquipamento"),

        botaoCategorias: document.getElementById("abrirListaCategorias"),
        listaCategorias: document.getElementById("listaCategorias")
    };

    let equipamentos = [];
    let salvando = false;

    // =========================================================
    // UTILITÁRIOS
    // =========================================================

    function escaparHTML(valor) {
        return String(valor ?? "").replace(/[&<>"']/g, caractere => ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;"
        })[caractere]);
    }

    function obterId(equipamento) {
        return equipamento.id_equipamento ?? equipamento.id;
    }

    function normalizarStatus(status) {
        const valor = String(status ?? "")
            .trim()
            .toUpperCase()
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "");

        const permitidos = [
            "DISPONIVEL",
            "EMPRESTADO",
            "MANUTENCAO",
            "INATIVO"
        ];

        return permitidos.includes(valor) ? valor : "DISPONIVEL";
    }

    function nomeStatus(status) {
        const nomes = {
            DISPONIVEL: "Disponível",
            EMPRESTADO: "Emprestado",
            MANUTENCAO: "Em manutenção",
            INATIVO: "Inativo"
        };

        return nomes[normalizarStatus(status)];
    }

    function mostrarMensagem(texto = "", tipo = "") {
        if (!el.mensagem) return;

        el.mensagem.textContent = texto;
        el.mensagem.className = tipo
            ? `mensagem ${tipo}`
            : "mensagem";
    }

    function mostrarMensagemFormulario(texto = "", tipo = "") {
        if (!el.mensagemFormulario) return;

        el.mensagemFormulario.textContent = texto;
        el.mensagemFormulario.className = tipo
            ? `mensagem ${tipo}`
            : "mensagem";
    }

    // =========================================================
    // CATEGORIAS
    // =========================================================

    function obterCategorias() {
        return [
            ...new Set(
                equipamentos
                    .map(item => String(item.categoria ?? "").trim())
                    .filter(Boolean)
            )
        ].sort((a, b) => a.localeCompare(b, "pt-BR"));
    }

    function fecharListaCategorias() {
        if (el.listaCategorias) {
            el.listaCategorias.hidden = true;
        }

        el.botaoCategorias?.setAttribute("aria-expanded", "false");
    }

    function selecionarCategoria(categoria) {
        if (!el.categoria) return;

        el.categoria.value = categoria;
        fecharListaCategorias();
        el.categoria.focus();
    }

    function renderizarListaCategorias() {
        if (!el.categoria || !el.listaCategorias) return;

        const termo = el.categoria.value
            .trim()
            .toLocaleLowerCase("pt-BR");

        const categorias = obterCategorias();

        const filtradas = categorias.filter(categoria =>
            categoria.toLocaleLowerCase("pt-BR").includes(termo)
        );

        el.listaCategorias.replaceChildren();

        if (filtradas.length === 0) {
            const item = document.createElement("li");

            item.className = "categoria-sem-resultado";
            item.textContent = termo
                ? "Nenhuma categoria encontrada. Podes cadastrar uma nova."
                : "Nenhuma categoria cadastrada.";

            item.setAttribute("role", "option");
            el.listaCategorias.appendChild(item);
        } else {
            filtradas.forEach(categoria => {
                const item = document.createElement("li");

                item.textContent = categoria;
                item.setAttribute("role", "option");
                item.tabIndex = 0;

                item.addEventListener("mousedown", evento => {
                    evento.preventDefault();
                    selecionarCategoria(categoria);
                });

                item.addEventListener("keydown", evento => {
                    if (evento.key === "Enter" || evento.key === " ") {
                        evento.preventDefault();
                        selecionarCategoria(categoria);
                    }
                });

                el.listaCategorias.appendChild(item);
            });
        }

        el.listaCategorias.hidden = false;
        el.botaoCategorias?.setAttribute("aria-expanded", "true");
    }

    function configurarListaCategorias() {
        if (
            !el.categoria ||
            !el.listaCategorias ||
            !el.botaoCategorias
        ) {
            console.warn(
                "Não foi possível configurar a lista de categorias. Confira o HTML."
            );
            return;
        }

        el.botaoCategorias.addEventListener("click", () => {
            if (el.listaCategorias.hidden) {
                renderizarListaCategorias();
            } else {
                fecharListaCategorias();
            }
        });

        el.categoria.addEventListener("focus", () => {
            renderizarListaCategorias();
        });

        el.categoria.addEventListener("input", () => {
            renderizarListaCategorias();
        });

        el.categoria.addEventListener("keydown", evento => {
            if (evento.key === "Escape") {
                fecharListaCategorias();
            }

            if (evento.key === "ArrowDown" && el.listaCategorias.hidden) {
                evento.preventDefault();
                renderizarListaCategorias();
                el.listaCategorias.querySelector('[role="option"]:not(.categoria-sem-resultado)')?.focus();
            }
        });

        document.addEventListener("click", evento => {
            if (!evento.target.closest(".categoria-container")) {
                fecharListaCategorias();
            }
        });
    }

    // =========================================================
    // FILTROS E LISTAGEM
    // =========================================================

    function aplicarFiltros() {
        const termo = (el.busca?.value ?? "")
            .trim()
            .toLocaleLowerCase("pt-BR");

        const statusFiltro = el.filtro?.value ?? "";

        const resultado = equipamentos.filter(equipamento => {
            const conteudo = [
                obterId(equipamento),
                equipamento.nome,
                equipamento.categoria,
                equipamento.descricao,
                equipamento.id_estoque
            ]
                .map(valor => String(valor ?? ""))
                .join(" ")
                .toLocaleLowerCase("pt-BR");

            const correspondeTexto = conteudo.includes(termo);

            const correspondeStatus =
                !statusFiltro ||
                normalizarStatus(equipamento.status_equip) ===
                    normalizarStatus(statusFiltro);

            return correspondeTexto && correspondeStatus;
        });

        renderizarEquipamentos(resultado);
    }

    function renderizarEquipamentos(lista) {
        if (!el.lista) return;

        el.lista.replaceChildren();

        if (lista.length === 0) {
            const vazio = document.createElement("div");

            vazio.className = "estado-vazio";
            vazio.textContent = equipamentos.length
                ? "Nenhum equipamento corresponde aos filtros."
                : "Nenhum equipamento cadastrado.";

            el.lista.appendChild(vazio);
            return;
        }

        lista.forEach(equipamento => {
            const id = obterId(equipamento);
            const status = normalizarStatus(equipamento.status_equip);

            const card = document.createElement("article");
            card.className = "card-equipamento";

            card.innerHTML = `
                <div class="card-cabecalho">
                    <div>
                        <span class="identificador">
                            Equipamento #${escaparHTML(id)}
                        </span>

                        <h3>${escaparHTML(equipamento.nome || "Sem nome")}</h3>
                    </div>

                    <span class="status status-${status.toLowerCase()}">
                        ${escaparHTML(nomeStatus(status))}
                    </span>
                </div>

                <div class="detalhes-equipamento">
                    <p>
                        <strong>Estoque:</strong>
                        ${escaparHTML(equipamento.id_estoque ?? "Não informado")}
                    </p>

                    <p>
                        <strong>Categoria:</strong>
                        ${escaparHTML(equipamento.categoria || "Não informada")}
                    </p>

                    <p>
                        <strong>Descrição:</strong>
                        ${escaparHTML(equipamento.descricao || "Não informada")}
                    </p>
                </div>

                <div class="acoes-card">
                    <button
                        type="button"
                        class="botao botao-editar"
                        data-acao="editar"
                        data-id="${escaparHTML(id)}"
                    >
                        Editar equipamento
                    </button>
                </div>
            `;

            el.lista.appendChild(card);
        });
    }

    async function carregarEquipamentos() {
        mostrarMensagem("Carregando equipamentos...");

        if (el.lista) {
            el.lista.replaceChildren();

            const carregando = document.createElement("div");
            carregando.className = "estado-vazio";
            carregando.textContent = "Carregando equipamentos...";

            el.lista.appendChild(carregando);
        }

        try {
            const resposta = await fetch(API_EQUIPAMENTOS, {
                method: "GET",
                headers: {
                    Accept: "application/json"
                }
            });

            if (!resposta.ok) {
                throw new Error(
                    `Erro ao consultar equipamentos: HTTP ${resposta.status}.`
                );
            }

            const dados = await resposta.json();

            if (!Array.isArray(dados)) {
                throw new Error(
                    "A API não retornou uma lista válida de equipamentos."
                );
            }

            equipamentos = dados;

            aplicarFiltros();
            mostrarMensagem();
        } catch (erro) {
            console.error(erro);

            if (el.lista) {
                el.lista.replaceChildren();

                const aviso = document.createElement("div");
                aviso.className = "estado-vazio";
                aviso.textContent =
                    "Não foi possível carregar os equipamentos.";

                el.lista.appendChild(aviso);
            }

            mostrarMensagem(
                erro.message || "Erro ao carregar equipamentos.",
                "mensagem-erro"
            );
        }
    }

    // =========================================================
    // MODAL
    // =========================================================

    function abrirModal(equipamento = null) {
        if (!el.modal || !el.formulario) return;

        el.formulario.reset();
        mostrarMensagemFormulario();
        fecharListaCategorias();

        if (equipamento) {
            el.id.value = obterId(equipamento) ?? "";
            el.nome.value = equipamento.nome ?? "";
            el.estoque.value = String(equipamento.id_estoque ?? "");
            el.categoria.value = equipamento.categoria ?? "";
            el.descricao.value = equipamento.descricao ?? "";
            el.status.value = normalizarStatus(
                equipamento.status_equip
            ).toLowerCase();

            if (el.tituloModal) {
                el.tituloModal.textContent = "Editar equipamento";
            }

            if (el.botaoSalvar) {
                el.botaoSalvar.textContent = "Salvar alterações";
            }
        } else {
            el.id.value = "";

            if (el.tituloModal) {
                el.tituloModal.textContent = "Cadastrar equipamento";
            }

            if (el.botaoSalvar) {
                el.botaoSalvar.textContent = "Cadastrar equipamento";
            }
        }

        el.modal.hidden = false;
        el.modal.setAttribute("aria-hidden", "false");
        el.nome?.focus();
    }

    function fecharModal() {
        if (!el.modal) return;

        el.modal.hidden = true;
        el.modal.setAttribute("aria-hidden", "true");

        fecharListaCategorias();
        mostrarMensagemFormulario();
    }

    // =========================================================
    // CADASTRO E EDIÇÃO
    // =========================================================

    async function salvarEquipamento(evento) {
        evento.preventDefault();

        if (salvando || !el.formulario?.reportValidity()) return;

        const id = el.id.value.trim();

        const dados = {
            id_estoque: Number(el.estoque.value),
            nome: el.nome.value.trim(),
            categoria: el.categoria.value.trim(),
            descricao: el.descricao.value.trim() || null,
            status_equip: normalizarStatus(el.status.value)
        };

        if (
            !dados.id_estoque ||
            !dados.nome ||
            !dados.categoria
        ) {
            mostrarMensagemFormulario(
                "Preencha o nome, o estoque e a categoria.",
                "mensagem-erro"
            );
            return;
        }

        salvando = true;

        if (el.botaoSalvar) {
            el.botaoSalvar.disabled = true;
            el.botaoSalvar.textContent = "Salvando...";
        }

        try {
            const url = id
                ? `${API_EQUIPAMENTOS}/${encodeURIComponent(id)}`
                : API_EQUIPAMENTOS;

            const resposta = await fetch(url, {
                method: id ? "PUT" : "POST",
                headers: {
                    "Content-Type": "application/json",
                    Accept: "application/json"
                },
                body: JSON.stringify(dados)
            });

            if (!resposta.ok) {
                let mensagemErro =
                    "Não foi possível salvar o equipamento.";

                try {
                    const erroAPI = await resposta.json();

                    if (erroAPI.detail) {
                        mensagemErro = Array.isArray(erroAPI.detail)
                            ? erroAPI.detail
                                .map(item => item.msg || JSON.stringify(item))
                                .join("; ")
                            : String(erroAPI.detail);
                    }
                } catch {
                    // A resposta pode não conter JSON.
                }

                throw new Error(mensagemErro);
            }

            fecharModal();
            await carregarEquipamentos();

            mostrarMensagem(
                id
                    ? "Equipamento atualizado com sucesso."
                    : "Equipamento cadastrado com sucesso.",
                "mensagem-sucesso"
            );
        } catch (erro) {
            console.error(erro);

            mostrarMensagemFormulario(
                erro.message || "Erro ao salvar o equipamento.",
                "mensagem-erro"
            );
        } finally {
            salvando = false;

            if (el.botaoSalvar) {
                el.botaoSalvar.disabled = false;
                el.botaoSalvar.textContent = id
                    ? "Salvar alterações"
                    : "Cadastrar equipamento";
            }
        }
    }

    // =========================================================
    // EVENTOS
    // =========================================================

    function configurarEventos() {
        el.botaoNovo?.addEventListener("click", () => abrirModal());

        el.botaoFechar?.addEventListener("click", fecharModal);
        el.botaoCancelar?.addEventListener("click", fecharModal);

        el.formulario?.addEventListener("submit", salvarEquipamento);

        el.busca?.addEventListener("input", aplicarFiltros);
        el.filtro?.addEventListener("change", aplicarFiltros);

        el.lista?.addEventListener("click", evento => {
            const botao = evento.target.closest('[data-acao="editar"]');

            if (!botao) return;

            const equipamento = equipamentos.find(item =>
                String(obterId(item)) === String(botao.dataset.id)
            );

            if (equipamento) {
                abrirModal(equipamento);
            }
        });

        el.modal?.addEventListener("click", evento => {
            if (evento.target === el.modal) {
                fecharModal();
            }
        });

        document.addEventListener("keydown", evento => {
            if (evento.key === "Escape" && el.modal && !el.modal.hidden) {
                fecharModal();
            }
        });
    }

    configurarListaCategorias();
    configurarEventos();
    carregarEquipamentos();

    window.abrirModalEquipamento = () => abrirModal();
});