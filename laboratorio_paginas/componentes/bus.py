"""Bus de referencias (la secuencia con su cabezal de lectura) y controles."""

from __future__ import annotations

import reflex as rx

from laboratorio_paginas.componentes.comunes import boton_icono, segmentos
from laboratorio_paginas.estado.app import VELOCIDADES, EstadoApp
from laboratorio_paginas.estado.vistas import ReferenciaVista

ETIQUETAS_VELOCIDAD = {"0.5": "0,5×", "1": "1×", "2": "2×", "4": "4×"}


def estado_paso(indice: rx.Var, paso: rx.Var) -> rx.Var:
    """«pasado», «actual» o «futuro» según el paso que se está mostrando."""
    return rx.cond(indice == paso, "actual", rx.cond(indice < paso, "pasado", "futuro"))


def _referencia(ref: ReferenciaVista, paso: rx.Var, interactiva: bool) -> rx.Component:
    contenido = (
        ref.texto,
        rx.cond(ref.escritura, rx.el.span("w", class_name="ref-w")),
        rx.el.span(class_name="ref-marca", data_fallo=ref.fallo, aria_hidden="true"),
    )
    if not interactiva:
        return rx.el.span(*contenido, class_name="ref", data_estado=estado_paso(ref.indice, paso))
    return rx.el.button(
        *contenido,
        class_name="ref",
        type="button",
        data_estado=estado_paso(ref.indice, paso),
        on_click=EstadoApp.ir_a(ref.indice),
        aria_label="Ir al paso " + ref.indice.to_string() + ", página " + ref.texto,
    )


def cinta(referencias: rx.Var, paso: rx.Var, interactiva: bool = True) -> rx.Component:
    """La secuencia como una tira con cabezal de lectura."""
    return rx.el.div(
        rx.el.div(
            rx.el.span(class_name="cabezal", data_oculto=paso == 0, aria_hidden="true"),
            rx.foreach(referencias, lambda ref: _referencia(ref, paso, interactiva)),
            class_name="bus-refs",
            style={"--paso": paso},
        ),
        class_name="bus-cinta",
    )


def controles() -> rx.Component:
    """Ir al inicio, anterior, reproducir/pausar, siguiente y velocidad."""
    return rx.el.div(
        rx.el.span(
            "Paso ",
            rx.el.strong(EstadoApp.paso),
            " de ",
            EstadoApp.total_pasos,
            class_name="contador-paso",
            aria_live="polite",
        ),
        boton_icono("skip-back", "Ir al inicio", EstadoApp.al_inicio, "boton-inicio"),
        boton_icono("chevron-left", "Paso anterior", EstadoApp.anterior, "boton-anterior"),
        rx.cond(
            EstadoApp.reproduciendo,
            boton_icono("pause", "Pausar", EstadoApp.alternar_reproduccion, "boton-reproducir", False, True),
            boton_icono("play", "Reproducir", EstadoApp.alternar_reproduccion, "boton-reproducir", False, True),
        ),
        boton_icono("chevron-right", "Siguiente paso", EstadoApp.siguiente, "boton-siguiente"),
        segmentos(
            "velocidad",
            [(v, ETIQUETAS_VELOCIDAD[v]) for v in VELOCIDADES],
            EstadoApp.velocidad,
            EstadoApp.set_velocidad,
            "Velocidad",
        ),
        class_name="controles",
    )


def bus() -> rx.Component:
    """Banda superior del laboratorio."""
    return rx.el.section(
        rx.el.div(
            rx.el.strong("Bus de referencias"),
            rx.el.span("Toca una referencia para saltar a ese paso. Atajos: espacio, ← y →."),
            class_name="bus-titulo",
        ),
        controles(),
        cinta(EstadoApp.referencias, EstadoApp.paso),
        class_name="bus lab-bus",
        aria_label="Secuencia y controles de reproducción",
        style={"--escala": EstadoApp.escala},
    )
