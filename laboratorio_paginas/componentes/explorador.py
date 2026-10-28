"""Ranking y mapa de calor del explorador."""

from __future__ import annotations

import reflex as rx

from laboratorio_paginas.componentes.comunes import campo, segmentos
from laboratorio_paginas.core.modelos import CONTADORES_PERMITIDOS, NOMBRES_ORDEN, OrdenReglas
from laboratorio_paginas.estado.app import EstadoApp
from laboratorio_paginas.estado.explorador import CeldaMapa, ExploradorEstado, FilaMapa, FilaRanking

ENVEJECIMIENTOS = (("0", "Apagado"), ("4", "Cada 4"), ("8", "Cada 8"))


def _cargar(historia: rx.Var, contador: rx.Var, envejecimiento: rx.Var, orden: rx.Var) -> rx.event.EventSpec:
    return EstadoApp.cargar_en_laboratorio(historia, contador, envejecimiento, orden)


def _fila_ranking(fila: FilaRanking) -> rx.Component:
    accion = _cargar(fila.historia, fila.contador, fila.envejecimiento, fila.orden)
    return rx.el.tr(
        rx.el.td(fila.posicion, class_name="num"),
        rx.el.td(fila.historia, class_name="num"),
        rx.el.td(fila.contador, class_name="num"),
        rx.el.td(fila.envejecimiento_texto),
        rx.el.td(fila.nombre_orden, rx.cond(fila.es_recomendada, rx.el.span(" (recomendada)", class_name="tenue"))),
        rx.el.td(fila.fallos, class_name="num"),
        rx.el.td(fila.tasa, class_name="num"),
        rx.el.td(fila.costo, class_name="num"),
        rx.el.td(fila.diferencia_fifo, class_name="num"),
        rx.el.td(rx.el.button("Cargar en el laboratorio", type="button", class_name="boton")),
        on_click=accion,
        data_clic="true",
        title="Cargar en el laboratorio",
    )


def ranking() -> rx.Component:
    """Tabla de las 10 mejores combinaciones."""
    return rx.el.div(
        rx.el.table(
            rx.el.thead(
                rx.el.tr(
                    rx.el.th("#", class_name="num"),
                    rx.el.th("k", class_name="num", title="Bits de historia"),
                    rx.el.th("C", class_name="num", title="Bits del contador"),
                    rx.el.th("Envejecimiento"),
                    rx.el.th("Orden"),
                    rx.el.th("Fallos", class_name="num"),
                    rx.el.th("% fallos", class_name="num"),
                    rx.el.th("Bits", class_name="num"),
                    rx.el.th("Frente a FIFO", class_name="num"),
                    rx.el.th(rx.el.span("Acción", class_name="solo-lector")),
                )
            ),
            rx.el.tbody(rx.foreach(ExploradorEstado.ranking, _fila_ranking)),
            class_name="tabla",
        ),
        class_name="tabla-cinta",
    )


def _celda(celda: CeldaMapa, orden: rx.Var, envejecimiento: rx.Var) -> rx.Component:
    return rx.el.button(
        celda.fallos,
        rx.cond(celda.etiqueta != "", rx.el.small(celda.etiqueta)),
        type="button",
        class_name="mapa-celda",
        data_marca=celda.marca,
        style={"background": celda.fondo, "color": celda.texto},
        on_click=_cargar(celda.historia, celda.contador, envejecimiento, orden),
        aria_label="k "
        + celda.historia.to_string()
        + ", C "
        + celda.contador.to_string()
        + " bits: "
        + celda.fallos.to_string()
        + " fallos. Cargar en el laboratorio.",
    )


def _fila_mapa(fila: FilaMapa) -> rx.Component:
    return rx.fragment(
        rx.el.div(fila.etiqueta, class_name="mapa-cabecera", data_fila="true"),
        rx.foreach(fila.celdas, lambda c: _celda(c, ExploradorEstado.orden_mapa, ExploradorEstado.env_mapa)),
    )


def mapa() -> rx.Component:
    """Mapa de calor historia × contador, con selectores de envejecimiento y orden."""
    return rx.el.div(
        rx.el.div(
            campo(
                "Envejecimiento",
                segmentos(
                    "env-mapa",
                    list(ENVEJECIMIENTOS),
                    ExploradorEstado.env_mapa,
                    ExploradorEstado.set_env_mapa,
                    "Envejecimiento del mapa",
                ),
            ),
            campo(
                "Orden",
                rx.el.select(
                    *[rx.el.option(NOMBRES_ORDEN[o], value=o.value) for o in OrdenReglas],
                    value=ExploradorEstado.orden_mapa,
                    on_change=ExploradorEstado.set_orden_mapa,
                    class_name="selector",
                    aria_label="Orden del mapa",
                ),
            ),
            class_name="config-fila",
            style={"gap": "var(--e-4)", "margin-bottom": "var(--e-4)", "align-items": "flex-end"},
        ),
        rx.el.div(
            rx.el.div("", class_name="mapa-cabecera"),
            *[rx.el.div(f"C {c} bits", class_name="mapa-cabecera") for c in CONTADORES_PERMITIDOS],
            rx.foreach(ExploradorEstado.mapa, _fila_mapa),
            class_name="mapa",
            role="grid",
            aria_label="Fallos por bits de historia (filas) y de contador (columnas)",
        ),
        rx.el.div(
            rx.el.span("Menos fallos"),
            rx.el.i(aria_hidden="true"),
            rx.el.span("Más fallos. Toca una celda para abrirla en el laboratorio."),
            class_name="mapa-escala",
        ),
    )
