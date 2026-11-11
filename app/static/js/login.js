"use strict";

/* =========================================
   CONFIGURAÇÕES
========================================= */

const URL_LOGIN = "/api/login";

const destinosPermitidos = [
    "/dashboard-user",
    "/dashboard-gestor",
    "/dashboard-admin"
];

/* =========================================
   ELEMENTOS DO FORMULÁRIO
========================================= */

const formulario = document.getElementById("formulario-login");
const campoEmail = document.getElementById("email");
const campoSenha = document.getElementById("senha");
const botaoSenha = document.getElementById("alternar-senha");
const botaoEntrar = document.getElementById("botao-entrar");
const mensagem = document.getElementById("mensagem-login");

/* =========================================
   ALTERNAR VISIBILIDADE DA SENHA
========================================= */

if (botaoSenha && campoSenha) {
    botaoSenha.addEventListener("click", (evento) => {
        evento.preventDefault();

        const mostrar = campoSenha.type === "password";

        campoSenha.type = mostrar ? "text" : "password";

        botaoSenha.setAttribute(
            "aria-label",
            mostrar ? "Ocultar senha" : "Mostrar senha"
        );

        botaoSenha.setAttribute("aria-pressed", String(mostrar));

        campoSenha.focus();
    });
}

/* =========================================
   REALIZAR LOGIN
========================================= */

if (
    formulario &&
    campoEmail &&
    campoSenha &&
    botaoEntrar &&
    mensagem
) {
    formulario.addEventListener("submit", (evento) => {
        evento.preventDefault();

        /* Limpa mensagens anteriores */
        mensagem.hidden = true;
        mensagem.textContent = "";

        /* Bloqueia o botão durante a requisição */
        botaoEntrar.disabled = true;
        botaoEntrar.textContent = "ENTRANDO...";

        /* Captura os dados */
        const usuario = campoEmail.value.trim();
        const senha = campoSenha.value;

        const corpo = JSON.stringify({
            usuario,
            senha
        });

        /* Envia os dados para o servidor */
        fetch(URL_LOGIN, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            credentials: "same-origin",
            cache: "no-store",
            body: corpo
        })

            /* Processa a resposta */
            .then((resposta) => {
                return resposta.json()
                    .catch(() => ({}))
                    .then((resultado) => ({
                        resposta,
                        resultado
                    }));
            })

            /* Verifica o resultado do login */
            .then(({ resposta, resultado }) => {

                /* Credenciais inválidas ou outro erro HTTP */
                if (!resposta.ok) {
                    throw new Error(
                        typeof resultado.detail === "string"
                            ? resultado.detail
                            : "E-mail ou senha incorretos. Verifique suas credenciais."
                    );
                }

                /* Verifica se o destino é permitido */
                if (
                    typeof resultado.url === "string" &&
                    destinosPermitidos.includes(resultado.url)
                ) {
                    window.location.assign(resultado.url);
                    return;
                }

                throw new Error(
                    "Login processado, mas o servidor retornou um destino inválido."
                );
            })

            /* Exibe mensagens de erro */
            .catch((erro) => {
                console.error("Falha ao realizar login:", erro);

                mensagem.textContent = erro.message ||
                    "Não foi possível conectar ao servidor. Tente novamente.";

                mensagem.hidden = false;
            })

            /* Restaura o botão */
            .finally(() => {
                botaoEntrar.disabled = false;
                botaoEntrar.textContent = "ENTRAR";
            });
    });

} else {
    console.error(
        "Login: não foi possível inicializar o formulário. " +
        "Verifique os IDs dos elementos no HTML."
    );
}