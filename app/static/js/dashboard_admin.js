
"use strict";

document.addEventListener("DOMContentLoaded", () => {

    // =====================================================
    // ELEMENTOS DO DASHBOARD
    // =====================================================

    const listaPedidos = document.getElementById("listaPedidos");
    const listaUsuarios = document.getElementById("listaUsuarios");
    const listaEquipamentos = document.getElementById("listaEquipamentos");

    // =====================================================
    // CONFIGURAÇÕES
    // =====================================================

    const API = {
        pedidos: "/api/admin/pedidos",
        usuarios: "/api/admin/usuarios",
        equipamentos: "/api/admin/equipamentos"
    };

    // =====================================================
    // FUNÇÕES AUXILIARES
    // =====================================================

    async function buscarDados(url) {

        const resposta = await fetch(url, {
            method: "GET",
            credentials: "same-origin",
            headers: {
                "Accept": "application/json"
            },
            cache: "no-store"
        });

        if (resposta.status === 401) {
            window.location.href = "/login";
            throw new Error("Sessão expirada.");
        }

        if (resposta.status === 403) {
            throw new Error("Você não tem permissão para acessar estes dados.");
        }

        if (!resposta.ok) {
            throw new Error(`Erro ao consultar ${url}: ${resposta.status}`);
        }

        return await resposta.json();
    }

    function criarCelula(texto) {
        const td = document.createElement("td");
        td.textContent = texto ?? "—";
        return td;
    }

    function criarMensagem(tbody, texto, quantidadeColunas) {

        if (!tbody) return;

        tbody.replaceChildren();

        const linha = document.createElement("tr");
        const celula = document.createElement("td");

        celula.colSpan = quantidadeColunas;
        celula.className = "mensagem-vazia";
        celula.textContent = texto;

        linha.appendChild(celula);
        tbody.appendChild(linha);
    }

    function formatarData(data) {

        if (!data) return "—";

        const dataConvertida = new Date(data);

        if (Number.isNaN(dataConvertida.getTime())) {
            return "—";
        }

        return dataConvertida.toLocaleDateString("pt-BR");
    }

    function normalizarTexto(valor) {
        return String(valor ?? "")
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "")
            .toLowerCase()
            .replace(/[^a-z0-9]+/g, "-")
            .replace(/^-|-$/g, "");
    }

    function criarStatus(status) {

        const span = document.createElement("span");

        const valor = String(status ?? "Não informado");
        const classe = normalizarTexto(valor);

        span.className = `status-badge status-${classe}`;
        span.textContent = valor.replaceAll("_", " ");

        return span;
    }

    // =====================================================
    // PEDIDOS RECENTES
    // =====================================================

    function renderizarPedidos(pedidos) {

        if (!listaPedidos) return;

        listaPedidos.replaceChildren();

        if (!Array.isArray(pedidos) || pedidos.length === 0) {
            criarMensagem(
                listaPedidos,
                "Nenhum pedido encontrado.",
                6
            );
            return;
        }

        pedidos.slice(0, 5).forEach(pedido => {

            const linha = document.createElement("tr");

            linha.appendChild(
                criarCelula(
                    pedido.id_pedido ?? pedido.id ?? "—"
                )
            );

            linha.appendChild(
                criarCelula(pedido.usuario)
            );

            linha.appendChild(
                criarCelula(pedido.equipamento)
            );

            linha.appendChild(
                criarCelula(formatarData(pedido.data_pedido))
            );

            const celulaStatus = document.createElement("td");
            celulaStatus.appendChild(
                criarStatus(pedido.status)
            );

            linha.appendChild(celulaStatus);

            const celulaAcoes = document.createElement("td");

            const link = document.createElement("a");
            link.href = "/admin_pedidos";
            link.className = "link-painel";
            link.textContent = "Ver pedidos";
            link.setAttribute(
                "aria-label",
                `Ver gerenciamento de pedidos`
            );

            celulaAcoes.appendChild(link);
            linha.appendChild(celulaAcoes);

            listaPedidos.appendChild(linha);
        });
    }

    // =====================================================
    // USUÁRIOS RECENTES
    // =====================================================

    function renderizarUsuarios(usuarios) {

        if (!listaUsuarios) return;

        listaUsuarios.replaceChildren();

        if (!Array.isArray(usuarios) || usuarios.length === 0) {
            criarMensagem(
                listaUsuarios,
                "Nenhum usuário cadastrado.",
                3
            );
            return;
        }

        usuarios.slice(0, 5).forEach(usuario => {

            const linha = document.createElement("tr");

            linha.appendChild(
                criarCelula(usuario.nome)
            );

            linha.appendChild(
                criarCelula(usuario.perfil)
            );

            const celulaStatus = document.createElement("td");

            celulaStatus.appendChild(
                criarStatus(
                    usuario.ativo ? "Ativo" : "Inativo"
                )
            );

            linha.appendChild(celulaStatus);

            listaUsuarios.appendChild(linha);
        });
    }

    // =====================================================
    // EQUIPAMENTOS RECENTES
    // =====================================================

    function renderizarEquipamentos(equipamentos) {

        if (!listaEquipamentos) return;

        listaEquipamentos.replaceChildren();

        if (!Array.isArray(equipamentos) || equipamentos.length === 0) {
            criarMensagem(
                listaEquipamentos,
                "Nenhum equipamento cadastrado.",
                3
            );
            return;
        }

        // Agrupa equipamentos com o mesmo nome.
        const agrupados = new Map();

        equipamentos.forEach(equipamento => {

            const nome = equipamento.nome || "Sem nome";

            if (!agrupados.has(nome)) {
                agrupados.set(nome, {
                    nome: nome,
                    quantidade: 0,
                    status: {}
                });
            }

            const grupo = agrupados.get(nome);

            grupo.quantidade++;

            const status = equipamento.status_equip || "Não informado";

            grupo.status[status] = (grupo.status[status] || 0) + 1;
        });

        const registros = Array.from(agrupados.values()).slice(0, 5);

        registros.forEach(equipamento => {

            const linha = document.createElement("tr");

            linha.appendChild(
                criarCelula(equipamento.nome)
            );

            linha.appendChild(
                criarCelula(
                    `${equipamento.quantidade} ${
                        equipamento.quantidade === 1 ? "unidade" : "unidades"
                    }`
                )
            );

            const celulaStatus = document.createElement("td");

            const resumoStatus = Object.entries(equipamento.status)
                .map(([status, quantidade]) => {
                    return `${quantidade} ${status.replaceAll("_", " ")}`;
                })
                .join(" / ");

            celulaStatus.textContent = resumoStatus;

            linha.appendChild(celulaStatus);

            listaEquipamentos.appendChild(linha);
        });
    }

    // =====================================================
    // CARREGAMENTO DOS DADOS
    // =====================================================

    async function carregarPedidos() {

        try {
            const pedidos = await buscarDados(API.pedidos);
            renderizarPedidos(pedidos);

        } catch (erro) {
            console.error("Erro ao carregar pedidos:", erro);

            criarMensagem(
                listaPedidos,
                "Não foi possível carregar os pedidos.",
                6
            );
        }
    }

    async function carregarUsuarios() {

        try {
            const usuarios = await buscarDados(API.usuarios);
            renderizarUsuarios(usuarios);

        } catch (erro) {
            console.error("Erro ao carregar usuários:", erro);

            criarMensagem(
                listaUsuarios,
                "Não foi possível carregar os usuários.",
                3
            );
        }
    }

    async function carregarEquipamentos() {

        try {
            const equipamentos = await buscarDados(API.equipamentos);
            renderizarEquipamentos(equipamentos);

        } catch (erro) {
            console.error("Erro ao carregar equipamentos:", erro);

            criarMensagem(
                listaEquipamentos,
                "Não foi possível carregar os equipamentos.",
                3
            );
        }
    }

    // =====================================================
    // INICIALIZAÇÃO
    // =====================================================

    async function inicializarDashboard() {

        await Promise.all([
            carregarPedidos(),
            carregarUsuarios(),
            carregarEquipamentos()
        ]);

    }

    inicializarDashboard();

});
