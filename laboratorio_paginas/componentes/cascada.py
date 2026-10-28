"""Panel de decisión: por qué salió cada página, regla por regla."""

from __future__ import annotations

import reflex as rx

from laboratorio_paginas.componentes.comunes import insignia
from laboratorio_paginas.componentes.marcador import marcador
from laboratorio_paginas.estado.app import EstadoApp
from laboratorio_paginas.estado.vistas import CandidataVista, PasoVista, ReglaVista


def _candidata(candidata: CandidataVista) -> rx.Component:
    return rx.el.span(
        rx.el.strong(candidata.pagina),
        rx.cond(candidata.detalle != "", rx.el.span(candidata.detalle, class_name="mono")),
        rx.cond(~candidata.sigue, rx.el.span("descartada", class_name="solo-lector")),
        class_name="candidata",
        data_sigue=candidata.sigue,
    )


def _regla(regla: ReglaVista, orden: rx.Var) -> rx.Component:
    return rx.el.li(
        rx.el.span(class_name="regla-numero", aria_hidden="true"),
        rx.el.div(
            rx.el.span(regla.nombre, class_name="regla-nombre"),
            rx.cond(regla.decidio, rx.el.span("decide", class_name="regla-decide")),
            class_name="regla-cabeza",
        ),
        rx.el.div(rx.foreach(regla.candidatas, _candidata), class_name="candidatas"),
        rx.el.span(regla.razon, class_name="regla-razon"),
        class_name="regla",
        data_decidio=regla.decidio,
        style={"--orden": orden},
    )


def _estado(paso: PasoVista) -> rx.Component:
    tipo = rx.cond(paso.inicial, "neutro", rx.cond(paso.acierto, "acierto", "fallo"))
    texto = rx.cond(paso.inicial, "Inicio", rx.cond(paso.acierto, "Acierto", "Fallo"))
    return rx.el.div(insignia(tipo, texto), rx.el.span(paso.resumen), class_name="decision-estado")


def _comparacion(paso: PasoVista, nombre: rx.Var) -> rx.Component:
    return rx.cond(
        ~paso.inicial,
        rx.el.p(
            rx.el.strong(nombre, " en este paso: "),
            rx.cond(
                paso.frase != "",
                paso.frase,
                rx.cond(paso.acierto, "acierto.", "fallo, entra en un marco libre."),
            ),
            class_name="frase-comparacion",
        ),
    )


def panel_decision(paso: PasoVista, paso_comparacion: PasoVista, nombre_comparacion: rx.Var) -> rx.Component:
    """Cascada animada del paso actual y lo que hizo el algoritmo de comparación."""
    return rx.el.section(
        rx.el.h2("Decisión"),
        rx.el.div(
            _estado(paso),
            rx.cond(
                paso.reglas.length() > 0,
                rx.el.ol(
                    rx.foreach(paso.reglas, lambda regla, i: _regla(regla, i)),
                    class_name="cascada",
                    aria_label="Cascada de reglas",
                ),
            ),
            rx.cond(paso.frase != "", rx.el.p(paso.frase, class_name="frase", data_animar="true")),
            _comparacion(paso_comparacion, nombre_comparacion),
            class_name="decision",
            key=paso.indice.to_string(),
            aria_live="polite",
        ),
        class_name="zona",
        style={"--escala": EstadoApp.escala},
    )


def panel_marcadores() -> rx.Component:
    """Marcadores de fallos que avanzan con el paso."""
    return rx.el.section(
        rx.el.h2("Marcador de fallos"),
        rx.el.div(
            marcador("Tu configuración", EstadoApp.digitos_config, "led"),
            marcador(EstadoApp.nombre_comparacion, EstadoApp.digitos_comparacion, "fallo"),
            class_name="marcadores",
        ),
        rx.el.p(
            "Óptimo al final: ",
            rx.el.strong(EstadoApp.resumen.fallos_optimo),
            " fallos. Es el mínimo posible, pero conoce el futuro.",
            class_name="tenue",
            style={"font-size": "var(--t-14)", "margin-top": "var(--e-3)"},
        ),
        class_name="zona",
        style={"--escala": EstadoApp.escala},
    )
