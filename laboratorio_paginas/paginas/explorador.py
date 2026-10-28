"""Pantalla del explorador de combinaciones."""

from __future__ import annotations

import reflex as rx

from laboratorio_paginas.componentes.explorador import mapa, ranking
from laboratorio_paginas.componentes.navegacion import marco_pagina
from laboratorio_paginas.componentes.panel_config import entrada_secuencia
from laboratorio_paginas.estado.explorador import ExploradorEstado as E

RUTA = "/explorador"


def _aviso() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.strong("Mejor para esta secuencia: se calculó viendo la secuencia completa, como el Óptimo"),
            rx.el.p(
                rx.el.span(E.mejor_descripcion),
                " da ",
                rx.el.strong(E.mejor_fallos),
                " fallos (FIFO: ",
                E.fallos_fifo,
                "). Sirve para saber hasta dónde se puede llegar, pero no es una configuración que "
                "un sistema real pueda elegir de antemano.",
            ),
            class_name="aviso",
        ),
        rx.el.div(
            rx.el.strong("Recomendada (fija, elegida con otras 500 secuencias)"),
            rx.el.p(
                rx.el.span(E.recomendada_descripcion),
                " da ",
                rx.el.strong(E.recomendada_fallos),
                " fallos en esta secuencia.",
            ),
            class_name="aviso",
            style={"border-color": "var(--placa-borde)"},
        ),
        class_name="avisos",
    )


def pagina() -> rx.Component:
    """Explorador completo."""
    return marco_pagina(
        RUTA,
        rx.el.div(
            rx.el.h1("Explorador"),
            rx.el.p(
                "Prueba todas las combinaciones de historia, contador, envejecimiento y orden de reglas "
                "en tu secuencia, sin repetir las que se comportan igual.",
            ),
            class_name="pagina-titulo",
        ),
        rx.el.div(
            rx.el.div(entrada_secuencia(), class_name="zona"),
            rx.el.div(
                _aviso(),
                rx.el.p(
                    E.combinaciones,
                    " combinaciones distintas probadas con ",
                    E.marcos,
                    " marcos y ",
                    E.total_pasos,
                    " referencias.",
                    class_name="tenue",
                    style={"margin-top": "var(--e-3)"},
                ),
            ),
            class_name="dos-columnas con-panel",
        ),
        rx.el.section(
            rx.el.h2("Las 10 mejores para esta secuencia"),
            rx.el.p("Desempate: menos bits y, si siguen iguales, el orden Propuesta."),
            ranking(),
            class_name="seccion",
        ),
        rx.el.section(
            rx.el.h2("Mapa de calor: historia × contador"),
            rx.el.p("Cada celda es una combinación; el número son sus fallos."),
            mapa(),
            class_name="seccion",
            style={"max-width": "640px"},
        ),
    )
