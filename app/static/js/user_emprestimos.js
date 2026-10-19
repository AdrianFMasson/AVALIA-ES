"use strict";

(() => {
    const pesquisa = document.getElementById("pesquisaEmprestimos");
    const filtro = document.getElementById("filtroStatus");
    const corpo = document.getElementById("corpoTabelaEmprestimos");
    const contador = document.getElementById("totalEmprestimos");
    const mensagem = document.getElementById("mensagemFiltro");

    function filtrarEmprestimos() {
        const termo = pesquisa.value.trim().toLocaleLowerCase("pt-BR");
        const statusSelecionado = filtro.value;
        const linhas = Array.from(corpo.querySelectorAll("tr[data-status]"));
        let totalVisivel = 0;

        linhas.forEach(linha => {
            const correspondeTexto = linha.textContent.toLocaleLowerCase("pt-BR").includes(termo);
            const correspondeStatus = !statusSelecionado || linha.dataset.status === statusSelecionado;
            const visivel = correspondeTexto && correspondeStatus;

            linha.hidden = !visivel;

            if (visivel) {
                totalVisivel++;
            }
        });

        contador.textContent = totalVisivel;
        mensagem.hidden = totalVisivel > 0 || linhas.length === 0;
    }

    pesquisa.addEventListener("input", filtrarEmprestimos);
    filtro.addEventListener("change", filtrarEmprestimos);
})();