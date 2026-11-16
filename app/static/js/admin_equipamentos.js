"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const API_EQUIPAMENTOS = "/api/admin/equipamentos";
    const API_CATEGORIAS = "/api/admin/categorias";

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
        botaoCancelar: document.getElementById("cancelarEquipamento")
    };

    let equipamentos = [];
    let categorias = [];
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

        return permitidos.includes(valor)
            ? valor
            : "DISPONIVEL";
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

    async function obterDetalheErro(resposta) {
        try {
            const erroAPI = await resposta.json();

            if (erroAPI.detail) {
                if (Array.isArray(erroAPI.detail)) {
                    return erroAPI.detail
                        .map(item => item.msg || JSON.stringify(item))
                        .join("; ");
                }

                return String(erroAPI.detail);
            }
        } catch {
            // A resposta pode não conter JSON.
        }

        return `O servidor retornou o erro HTTP ${resposta.status}.`;
    }

    // =========================================================
    // CATEGORIAS
    // =========================================================

    function preencherCategorias(idSelecionado = "") {
        if (!el.categoria) return;

        const valorAnterior = String(idSelecionado || "");

        el.categoria.replaceChildren();

        const opcaoInicial = document.createElement("option");
        opcaoInicial.value = "";
        opcaoInicial.textContent = "Selecione uma categoria";

        el.categoria.appendChild(opcaoInicial);

        categorias.forEach(categoria => {
            const opcao = document.createElement("option");

            opcao.value = String(categoria.id_categoria);
            opcao.textContent = categoria.nome;

            el.categoria.appendChild(opcao);
        });

        if (
            valorAnterior &&
            categorias.some(
                categoria =>
                    String(categoria.id_categoria) === valorAnterior
            )
        ) {
            el.categoria.value = valorAnterior;
        } else {
            el.categoria.value = "";
        }
    }

    async function carregarCategorias(idSelecionado = "") {
        if (!el.categoria) return false;

        try {
            const resposta = await fetch(API_CATEGORIAS, {
                method: "GET",
                headers: {
                    Accept: "application/json"
                }
            });

            if (!resposta.ok) {
                throw new Error(
                    await obterDetalheErro(resposta)
                );
            }

            const dados = await resposta.json();

            if (!Array.isArray(dados)) {
                throw new Error(
                    "A API não retornou uma lista válida de categorias."
                );
            }

            categorias = dados.filter(categoria =>
                categoria.ativo === true
            );

            categorias.sort((a, b) =>
                String(a.nome).localeCompare(
                    String(b.nome),
                    "pt-BR"
                )
            );

            preencherCategorias(idSelecionado);

            return true;

        } catch (erro) {
            console.error("Erro ao carregar categorias:", erro);

            categorias = [];
            preencherCategorias();

            mostrarMensagemFormulario(
                "Não foi possível carregar as categorias. Verifique se existem categorias cadastradas e ativas.",
                "mensagem-erro"
            );

            return false;
        }
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
                equipamento.id_estoque,
                equipamento.id_categoria
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

                        <h3>
                            ${escaparHTML(equipamento.nome || "Sem nome")}
                        </h3>
                    </div>

                    <span class="status status-${status.toLowerCase()}">
                        ${escaparHTML(nomeStatus(status))}
                    </span>
                </div>

                <div class="detalhes-equipamento">

                    <p>
                        <strong>Estoque:</strong>
                        ${escaparHTML(
                            equipamento.id_estoque ?? "Não informado"
                        )}
                    </p>

                    <p>
                        <strong>Categoria:</strong>
                        ${escaparHTML(
                            equipamento.categoria || "Não informada"
                        )}
                    </p>

                    <p>
                        <strong>Descrição:</strong>
                        ${escaparHTML(
                            equipamento.descricao || "Não informada"
                        )}
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

    // =========================================================
    // CARREGAR EQUIPAMENTOS
    // =========================================================

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
                    await obterDetalheErro(resposta)
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
            console.error("Erro ao carregar equipamentos:", erro);

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

    async function abrirModal(equipamento = null) {
        if (!el.modal || !el.formulario) return;

        if (salvando) return;

        el.formulario.reset();

        mostrarMensagemFormulario();

        const idCategoria = equipamento
            ? equipamento.id_categoria
            : "";

        const categoriasCarregadas = await carregarCategorias(
            idCategoria
        );

        if (!categoriasCarregadas) {
            return;
        }

        if (equipamento) {
            el.id.value = obterId(equipamento) ?? "";

            el.nome.value = equipamento.nome ?? "";

            el.estoque.value = String(
                equipamento.id_estoque ?? ""
            );

            el.categoria.value = String(
                equipamento.id_categoria ?? ""
            );

            el.descricao.value = equipamento.descricao ?? "";

            el.status.value = normalizarStatus(
                equipamento.status_equip
            );

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

        if (salvando) return;

        el.modal.hidden = true;

        el.modal.setAttribute("aria-hidden", "true");

        mostrarMensagemFormulario();
    }

    // =========================================================
    // CADASTRAR E EDITAR EQUIPAMENTOS
    // =========================================================

    async function salvarEquipamento(evento) {
        evento.preventDefault();

        if (salvando || !el.formulario) return;

        if (!el.formulario.reportValidity()) return;

        const id = el.id.value.trim();

        const idEstoque = Number(el.estoque.value);
        const idCategoria = Number(el.categoria.value);

        const dados = {
            id_estoque: idEstoque,
            id_categoria: idCategoria,
            nome: el.nome.value.trim(),
            descricao: el.descricao.value.trim() || null,
            status_equip: normalizarStatus(el.status.value)
        };

        if (
            !dados.id_estoque ||
            !dados.id_categoria ||
            !dados.nome
        ) {
            mostrarMensagemFormulario(
                "Preencha o nome, o estoque e selecione uma categoria.",
                "mensagem-erro"
            );

            return;
        }

        const categoriaExiste = categorias.some(
            categoria =>
                Number(categoria.id_categoria) === dados.id_categoria
        );

        if (!categoriaExiste) {
            mostrarMensagemFormulario(
                "Selecione uma categoria cadastrada e ativa.",
                "mensagem-erro"
            );

            return;
        }

        salvando = true;

        if (el.botaoSalvar) {
            el.botaoSalvar.disabled = true;
            el.botaoSalvar.textContent = "Salvando...";
        }

        if (el.botaoCancelar) {
            el.botaoCancelar.disabled = true;
        }

        if (el.botaoFechar) {
            el.botaoFechar.disabled = true;
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
                throw new Error(
                    await obterDetalheErro(resposta)
                );
            }

            fecharModalAposSalvar();

            await carregarEquipamentos();

            mostrarMensagem(
                id
                    ? "Equipamento atualizado com sucesso."
                    : "Equipamento cadastrado com sucesso.",
                "mensagem-sucesso"
            );

        } catch (erro) {
            console.error("Erro ao salvar equipamento:", erro);

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

            if (el.botaoCancelar) {
                el.botaoCancelar.disabled = false;
            }

            if (el.botaoFechar) {
                el.botaoFechar.disabled = false;
            }
        }
    }

    function fecharModalAposSalvar() {
        if (!el.modal) return;

        el.modal.hidden = true;

        el.modal.setAttribute("aria-hidden", "true");

        mostrarMensagemFormulario();
    }

    // =========================================================
    // EVENTOS
    // =========================================================

    function configurarEventos() {
        el.botaoNovo?.addEventListener("click", () => {
            abrirModal();
        });

        el.botaoFechar?.addEventListener("click", fecharModal);

        el.botaoCancelar?.addEventListener("click", fecharModal);

        el.formulario?.addEventListener(
            "submit",
            salvarEquipamento
        );

        el.busca?.addEventListener("input", aplicarFiltros);

        el.filtro?.addEventListener("change", aplicarFiltros);

        el.lista?.addEventListener("click", evento => {
            const botao = evento.target.closest(
                '[data-acao="editar"]'
            );

            if (!botao) return;

            const equipamento = equipamentos.find(item =>
                String(obterId(item)) === String(botao.dataset.id)
            );

            if (equipamento) {
                abrirModal(equipamento);
            }
        });

        el.modal?.addEventListener("click", evento => {
            if (
                evento.target === el.modal &&
                !salvando
            ) {
                fecharModal();
            }
        });

        document.addEventListener("keydown", evento => {
            if (
                evento.key === "Escape" &&
                el.modal &&
                !el.modal.hidden &&
                !salvando
            ) {
                fecharModal();
            }
        });
    }

    // =========================================================
    // INICIALIZAÇÃO
    // =========================================================

    configurarEventos();

    carregarEquipamentos();

});