"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const botoesNavegacao = document.querySelectorAll("[data-tab]");
    const paineis = document.querySelectorAll(".tab-panel");
    const tituloPagina = document.getElementById("page-title");
    const mensagem = document.getElementById("feedback-message");

    const titulos = {
        "visao-geral": "Visão geral",
        "usuarios": "Usuários",
        "equipamentos": "Equipamentos",
        "pedidos": "Pedidos"
    };

    function mostrarMensagem(texto, tipo = "") {
        if (!mensagem) {
            return;
        }

        mensagem.textContent = texto;
        mensagem.className = "feedback-message";

        if (tipo) {
            mensagem.classList.add(tipo);
        }

        mensagem.hidden = false;
    }

    function abrirAba(nomeAba) {
        const painelAlvo = document.getElementById(`tab-${nomeAba}`);

        if (!painelAlvo) {
            return;
        }

        paineis.forEach((painel) => {
            const ativo = painel === painelAlvo;

            painel.classList.toggle("active", ativo);
            painel.hidden = !ativo;
        });

        botoesNavegacao.forEach((botao) => {
            const ativo = botao.dataset.tab === nomeAba;

            botao.classList.toggle("active", ativo);
            botao.setAttribute("aria-selected", String(ativo));
        });

        if (tituloPagina) {
            tituloPagina.textContent = titulos[nomeAba] || "Painel administrativo";
        }

        if (mensagem) {
            mensagem.hidden = true;
            mensagem.textContent = "";
        }
    }

    // Navegação pelas abas.
    botoesNavegacao.forEach((botao) => {
        botao.addEventListener("click", () => {
            abrirAba(botao.dataset.tab);
        });
    });

    // Atalhos da visão geral.
    document.querySelectorAll("[data-open-tab]").forEach((botao) => {
        botao.addEventListener("click", () => {
            abrirAba(botao.dataset.openTab);
        });
    });

    // Pesquisa local nas tabelas.
    document.querySelectorAll("[data-search]").forEach((campo) => {
        campo.addEventListener("input", () => {
            const tabelaId = campo.dataset.search;
            const tabela = document.getElementById(tabelaId);

            if (!tabela) {
                return;
            }

            const termo = campo.value.trim().toLocaleLowerCase("pt-BR");
            const linhas = tabela.querySelectorAll("tbody tr");

            linhas.forEach((linha) => {
                // Mantém visíveis as linhas informativas sem registros.
                if (linha.querySelector(".empty-state")) {
                    linha.hidden = true;
                    return;
                }

                const conteudo = linha.textContent.toLocaleLowerCase("pt-BR");
                linha.hidden = !conteudo.includes(termo);
            });
        });
    });

    // Os cadastros serão ligados às rotas administrativas depois.
    document.querySelectorAll("[data-action]").forEach((botao) => {
        botao.addEventListener("click", () => {
            const acoes = {
                "criar-usuario":
                    "O cadastro de usuários será habilitado após a implementação da rota administrativa.",
                "criar-equipamento":
                    "O cadastro de equipamentos será habilitado após a implementação da rota administrativa."
            };

            mostrarMensagem(
                acoes[botao.dataset.action] ||
                    "Esta operação ainda não está disponível.",
                "error"
            );
        });
    });

    // Inicializa a interface.
    abrirAba("visao-geral");
});