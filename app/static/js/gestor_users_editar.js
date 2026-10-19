"use strict";

const formEditarUsuario = document.getElementById("formEditarUsuario");
const mensagemTela = document.getElementById("mensagemTela");
const botaoSalvar = document.getElementById("botaoSalvar");
const usuarioId = document.getElementById("id_usuario").value;
const campoContato = document.getElementById("contato");

function mostrarMensagem(texto, tipo = "") {
    mensagemTela.textContent = texto;
    mensagemTela.className = tipo ? `mensagem ${tipo}` : "mensagem";
}

function formatarContato(valor) {
    const numeros = valor.replace(/\D/g, "").slice(0, 11);

    if (numeros.length === 0) return "";
    if (numeros.length <= 2) return `(${numeros}`;
    if (numeros.length <= 7) return `(${numeros.slice(0, 2)})${numeros.slice(2)}`;

    return `(${numeros.slice(0, 2)})${numeros.slice(2, 7)}-${numeros.slice(7)}`;
}

campoContato.value = formatarContato(campoContato.value);

campoContato.addEventListener("input", () => {
    campoContato.value = formatarContato(campoContato.value);
});

formEditarUsuario.addEventListener("submit", async evento => {
    evento.preventDefault();
    mostrarMensagem("");

    const nome = document.getElementById("nome").value.trim();
    const contato = campoContato.value.replace(/\D/g, "");
    const email = document.getElementById("email").value.trim();
    const idPerfil = Number(document.getElementById("id_perfil").value);
    const ativo = document.getElementById("status").value === "true";
    const senha = document.getElementById("senha").value;

    if (!nome || !email) {
        mostrarMensagem("Preencha o nome e o e-mail.", "mensagem-erro");
        return;
    }

    if (contato && contato.length !== 11) {
        mostrarMensagem("Informe o contato com DDD e 11 dígitos, no formato (XX)XXXXX-XXXX.", "mensagem-erro");
        campoContato.focus();
        return;
    }

    if (senha && senha.trim()) {
        const senhaValida = senha.length >= 6 &&
            /[A-Z]/.test(senha) &&
            /[a-z]/.test(senha) &&
            /[^A-Za-z0-9]/.test(senha);

        if (!senhaValida) {
            mostrarMensagem("A nova senha deve ter pelo menos 6 caracteres, uma letra maiúscula, uma minúscula e um caractere especial.", "mensagem-erro");
            return;
        }
    }

    const dados = {
        nome,
        contato: contato || null,
        email,
        id_perfil: idPerfil,
        ativo
    };

    if (senha && senha.trim()) {
        dados.senha = senha;
    }

    botaoSalvar.disabled = true;
    botaoSalvar.textContent = "Salvando...";

    try {
        const resposta = await fetch(`/usuarios/${encodeURIComponent(usuarioId)}`, {
            method: "PUT",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(dados)
        });

        const resultado = await resposta.json().catch(() => ({}));

        if (!resposta.ok) {
            const detalhe = typeof resultado.detail === "string"
                ? resultado.detail
                : `Não foi possível salvar as alterações (HTTP ${resposta.status}).`;

            throw new Error(detalhe);
        }

        mostrarMensagem("Alterações salvas com sucesso.", "mensagem-sucesso");

        setTimeout(() => {
            window.location.href = "/gestor_users";
        }, 1000);
    } catch (erro) {
        mostrarMensagem(erro.message || "Erro de conexão com o servidor.", "mensagem-erro");
    } finally {
        botaoSalvar.disabled = false;
        botaoSalvar.textContent = "Salvar alterações";
    }
});