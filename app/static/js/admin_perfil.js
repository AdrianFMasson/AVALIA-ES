"use strict";

const API_PERFIS = "/api/admin/perfis";

const elementos = {
    formulario: document.getElementById("campos-perfil"),
    tituloModal: document.getElementById("tituloModal"),
    btnNovo: document.getElementById("novoPerfil"),
    lista: document.getElementById("listaPerfis"),
    id: document.getElementById("perfilId"),
    perfil: document.getElementById("perfilUsuario"),
    descricao: document.getElementById("descricaoPerfil")
};


async function salvarDadosDePerfil(dadosDoFormulario, idPerfil = null) {
    try {
       
        const url = idPerfil ? `${API_PERFIS}/${idPerfil}` : API_PERFIS;
        const metodo = idPerfil ? "PUT" : "POST";

        const resposta = await fetch(url, {
            method: metodo,
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(dadosDoFormulario)
        });

        if (!resposta.ok) {
            const erroDetalhes = await resposta.json().catch(() => ({}));
            throw new Error(erroDetalhes.detail || `Erro HTTP: ${resposta.status}`);
        }

        const resultado = await resposta.json();
        console.log("Salvo com sucesso:", resultado);
        alert("Perfil salvo com sucesso!");

        limparFormulario();
        carregarPerfis(); // Atualiza a lista na tela após salvar

    } catch (erro) {
        console.error("Erro ao salvar perfil:", erro);
        alert(`Não foi possível salvar: ${erro.message}`);
    }
}

async function carregarPerfis() {
    if (!elementos.lista) return;

    try {
        const resposta = await fetch(API_PERFIS);
        if (!resposta.ok) throw new Error("Erro ao buscar perfis");

        const perfis = await resposta.json();
        elementos.lista.innerHTML = ""; // Limpa a lista atual

        if (perfis.length === 0) {
            elementos.lista.innerHTML = "<p>Nenhum perfil cadastrado ainda.</p>";
            return;
        }

        perfis.forEach(item => {
            const card = document.createElement("div");
            card.className = "item-perfil";
            card.innerHTML = `
                <strong>${item.perfil}</strong> - <span>${item.descricao}</span>
            `;
            elementos.lista.appendChild(card);
        });

    } catch (erro) {
        console.error("Erro ao carregar lista:", erro);
    }
}

function limparFormulario() {
    elementos.formulario.reset();
    elementos.id.value = "";
    if (elementos.tituloModal) {
        elementos.tituloModal.textContent = "Novo Perfil";
    }
}

document.addEventListener("DOMContentLoaded", () => {
    carregarPerfis();
    if (elementos.formulario) {
        elementos.formulario.addEventListener("submit", (evento) => {
            evento.preventDefault();

            const idAtual = elementos.id.value.trim();
            const dados = {
                perfil: elementos.perfil.value,
                descricao: elementos.descricao.value.trim()
            };

            salvarDadosDePerfil(dados, idAtual || null);
        });
    }
    if (elementos.btnNovo) {
        elementos.btnNovo.addEventListener("click", limparFormulario);
    }
});
