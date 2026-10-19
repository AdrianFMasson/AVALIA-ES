"use strict";

window.addEventListener("pageshow", (evento) => {
    if (evento.persisted) {
        window.location.reload();
    }
});