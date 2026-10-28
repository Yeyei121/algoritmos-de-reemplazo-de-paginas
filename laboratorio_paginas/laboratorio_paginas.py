"""Aplicación Reflex: registro de páginas, hojas de estilo y atajos de teclado."""

from __future__ import annotations

import reflex as rx

from laboratorio_paginas.estado.inicio import InicioEstado
from laboratorio_paginas.estilos.tema import HOJAS_DE_ESTILO, SCRIPTS
from laboratorio_paginas.paginas import explorador, inicio, laboratorio, marcos, validacion

DESCRIPCION = "FIFO con bits adicionales de referencia comparado con el original, paso a paso."

app = rx.App(
    stylesheets=list(HOJAS_DE_ESTILO),
    head_components=[rx.script(src=src) for src in SCRIPTS],
    html_lang="es",
)

app.add_page(
    inicio.pagina,
    route=inicio.RUTA,
    title="Laboratorio de reemplazo de páginas",
    description=DESCRIPCION,
    on_load=InicioEstado.al_cargar,
)
for modulo, nombre in (
    (laboratorio, "Laboratorio"),
    (explorador, "Explorador"),
    (marcos, "Marcos"),
    (validacion, "Validación"),
):
    app.add_page(modulo.pagina, route=modulo.RUTA, title=f"{nombre} | Reemplazo de páginas", description=DESCRIPCION)
