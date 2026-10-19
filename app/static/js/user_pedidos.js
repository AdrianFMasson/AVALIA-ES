"use strict";

(() => {
    const pesquisa = document.getElementById("pesquisaPedidos");
    const filtroStatus = document.getElementById("filtroStatus");
    const corpoTabela = document.getElementById("corpoTabelaPedidos");
    const contador = document.getElementById("totalPedidos");
    const mensagemFiltro = document.getElementById("mensagemFiltro");

    function filtrarPedidos() {
        const termo = pesquisa.value.trim().toLocaleLowerCase("pt-BR");
        const statusSelecionado = filtroStatus.value;
        const linhas = Array.from(corpoTabela.querySelectorAll("tr[data-status]"));
        let visiveis = 0;

        linhas.forEach(linha => {
            const correspondeTexto = linha.textContent.toLocaleLowerCase("pt-BR").includes(termo);
            const correspondeStatus = !statusSelecionado || linha.dataset.status === statusSelecionado;
            const mostrar = correspondeTexto && correspondeStatus;

            linha.hidden = !mostrar;

            if (mostrar) {
                visiveis++;
            }
        });

        contador.textContent = visiveis;
        mensagemFiltro.hidden = visiveis > 0 || linhas.length === 0;
    }

    pesquisa.addEventListener("input", filtrarPedidos);
    filtroStatus.addEventListener("change", filtrarPedidos);
})();