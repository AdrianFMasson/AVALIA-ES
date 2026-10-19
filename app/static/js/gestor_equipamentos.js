const listaEquipamentos = document.getElementById("listaEquipamentos");
const mensagemTela = document.getElementById("mensagemTela");
const busca = document.getElementById("busca");
const filtroStatus = document.getElementById("filtroStatus");
const quantidadeExibida = document.getElementById("quantidadeExibida");
const botaoAtualizar = document.getElementById("botaoAtualizar");
let equipamentos = [];

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
        DISPONIVEL: "Disponível",
        EMPRESTADO: "Emprestado",
        MANUTENCAO: "Em manutenção",
        INATIVO: "Inativo"
    })[status] || status || "Não informado";
}

function atualizarResumo() {
    document.getElementById("totalEquipamentos").textContent = equipamentos.length;
    document.getElementById("totalDisponiveis").textContent = equipamentos.filter(e => e.status_equip === "DISPONIVEL").length;
    document.getElementById("totalEmprestados").textContent = equipamentos.filter(e => e.status_equip === "EMPRESTADO").length;
    document.getElementById("totalManutencao").textContent = equipamentos.filter(e => e.status_equip === "MANUTENCAO").length;
    document.getElementById("totalInativos").textContent = equipamentos.filter(e => e.status_equip === "INATIVO").length;
}

function renderizarEquipamentos() {
    const termo = busca.value.trim().toLocaleLowerCase("pt-BR");
    const statusSelecionado = filtroStatus.value;

    const filtrados = equipamentos.filter(e => {
        const id = String(e.id_equipamento ?? "").toLocaleLowerCase("pt-BR");
        const nome = String(e.nome ?? "").toLocaleLowerCase("pt-BR");
        const correspondeBusca = !termo || id.includes(termo) || nome.includes(termo);
        const correspondeStatus = !statusSelecionado || e.status_equip === statusSelecionado;
        return correspondeBusca && correspondeStatus;
    });

    if (!filtrados.length) {
        listaEquipamentos.innerHTML = '<tr><td colspan="5" class="vazio">Nenhum equipamento encontrado.</td></tr>';
        quantidadeExibida.textContent = "Nenhum registro para exibir.";
        return;
    }

    listaEquipamentos.innerHTML = filtrados.map(e => `
        <tr>
            <td>#${escaparHTML(e.id_equipamento)}</td>
            <td>${escaparHTML(e.nome)}</td>
            <td>${escaparHTML(e.categoria)}</td>
            <td>${escaparHTML(e.descricao || "—")}</td>
            <td><span class="etiqueta-status status-${escaparHTML(e.status_equip)}">${escaparHTML(nomeStatus(e.status_equip))}</span></td>
        </tr>
    `).join("");

    quantidadeExibida.textContent = `Exibindo ${filtrados.length} de ${equipamentos.length} equipamentos.`;
}

async function carregarEquipamentos() {
    listaEquipamentos.innerHTML = '<tr><td colspan="5" class="vazio">Carregando equipamentos...</td></tr>';
    quantidadeExibida.textContent = "Carregando...";
    mostrarMensagem("");
    botaoAtualizar.disabled = true;

    try {
        const resposta = await fetch("/equipamentos");
        const resultado = await resposta.json().catch(() => null);

        if (!resposta.ok) {
            throw new Error("Não foi possível carregar os equipamentos. Tente novamente.");
        }

        if (!Array.isArray(resultado)) {
            throw new Error("A API não retornou uma lista válida de equipamentos.");
        }

        equipamentos = resultado;
        atualizarResumo();
        renderizarEquipamentos();
    } catch (erro) {
        listaEquipamentos.innerHTML = '<tr><td colspan="5" class="vazio">Erro ao carregar os equipamentos.</td></tr>';
        quantidadeExibida.textContent = "";
        mostrarMensagem(erro.message || "Erro de conexão com o servidor.", "mensagem-erro");
    } finally {
        botaoAtualizar.disabled = false;
    }
}

busca.addEventListener("input", renderizarEquipamentos);
filtroStatus.addEventListener("change", renderizarEquipamentos);
botaoAtualizar.addEventListener("click", carregarEquipamentos);

carregarEquipamentos();