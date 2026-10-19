"use strict";

const formulario = document.getElementById("formulario-login");
const campoEmail = document.getElementById("email");
const campoSenha = document.getElementById("senha");
const botaoSenha = document.getElementById("alternar-senha");
const botaoEntrar = document.getElementById("botao-entrar");
const mensagem = document.getElementById("mensagem-login");

botaoSenha.addEventListener("click", () => {
    const mostrar = campoSenha.type === "password";
    campoSenha.type = mostrar ? "text" : "password";
    botaoSenha.setAttribute("aria-label", mostrar ? "Ocultar senha" : "Mostrar senha");
    botaoSenha.setAttribute("aria-pressed", String(mostrar));
    campoSenha.focus();
});

formulario.addEventListener("submit", async evento => {
    evento.preventDefault();
    mensagem.hidden = true;
    mensagem.textContent = "";
    botaoEntrar.disabled = true;
    botaoEntrar.textContent = "ENTRANDO...";

    try {
        const resposta = await fetch("/api/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            credentials: "same-origin",
            cache: "no-store",
            body: JSON.stringify({
                usuario: campoEmail.value.trim(),
                senha: campoSenha.value
            })
        });

        const resultado = await resposta.json().catch(() => ({}));

        if (!resposta.ok) {
            mensagem.textContent = typeof resultado.detail === "string"
                ? resultado.detail
                : "Não foi possível entrar. Verifique seu e-mail e sua senha.";
            mensagem.hidden = false;
            return;
        }

        if (typeof resultado.url === "string" && resultado.url.startsWith("/")) {
            window.location.href = resultado.url;
            return;
        }

        mensagem.textContent = "Login processado, mas o servidor não informou uma página de destino válida.";
        mensagem.hidden = false;
    } catch (erro) {
        mensagem.textContent = "Não foi possível conectar ao servidor. Tente novamente.";
        mensagem.hidden = false;
    } finally {
        botaoEntrar.disabled = false;
        botaoEntrar.textContent = "ENTRAR";
    }
});