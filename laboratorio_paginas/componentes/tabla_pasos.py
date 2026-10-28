"""Tabla paso a paso al estilo del Excel del profesor.

Cada columna es una referencia y cada fila un marco; debajo van «Sale» y «Fallo».
Las dos tablas comparten la misma rejilla, así los conectores de «fallo evitado»
quedan alineados con su columna.
"""

from __future__ import annotations

import reflex as rx

from laboratorio_paginas.componentes.bus import estado_paso
from laboratorio_paginas.componentes.comunes import boton_icono
from laboratorio_paginas.estado.app import EstadoApp
from laboratorio_paginas.estado.vistas import CeldaVista, ColumnaVista

TEXTO_DIFERENCIA = (("evitado", "fallo evitado"), ("perdido", "fallo de más"))


def _celda(celda: CeldaVista, columna: ColumnaVista) -> rx.Component:
    return rx.el.div(
        rx.el.strong(celda.pagina),
        rx.cond(celda.detalle != "", rx.el.small(celda.detalle)),
        class_name="tp-celda",
        data_col=estado_paso(columna.indice, EstadoApp.paso),
        data_evento=celda.evento,
        data_cambio=celda.cambio,
        data_puntero=celda.puntero,
    )


def _tabla(titulo: rx.Var | str, detalle: rx.Var | str, columnas: rx.Var) -> rx.Component:
    paso = EstadoApp.paso
    return rx.el.div(
        rx.el.div(rx.el.strong(titulo), rx.el.span(detalle, class_name="tenue"), class_name="tp-titulo"),
        rx.el.div("Referencia", class_name="tp-etiqueta"),
        rx.foreach(
            columnas,
            lambda col: rx.el.div(col.referencia, class_name="tp-ref", data_col=estado_paso(col.indice, paso)),
        ),
        rx.foreach(
            EstadoApp.filas_marcos,
            lambda etiqueta, m: rx.fragment(
                rx.el.div(etiqueta, class_name="tp-etiqueta"),
                rx.foreach(columnas, lambda col: _celda(col.celdas[m], col)),
            ),
        ),
        rx.el.div("Sale", class_name="tp-etiqueta"),
        rx.foreach(
            columnas,
            lambda col: rx.el.div(
                rx.el.span(col.sale), class_name="tp-celda tp-sale", data_col=estado_paso(col.indice, paso)
            ),
        ),
        rx.el.div("Fallo", class_name="tp-etiqueta"),
        rx.foreach(
            columnas,
            lambda col: rx.el.div(
                rx.cond(col.fallo, rx.el.span("Fallo")),
                class_name="tp-celda tp-fallo",
                data_col=estado_paso(col.indice, paso),
            ),
        ),
        class_name="tabla-pasos",
        style={"--columnas": EstadoApp.total_pasos},
        role="table",
        aria_label=titulo,
    )


def _conectores() -> rx.Component:
    paso = EstadoApp.paso
    return rx.el.div(
        rx.el.div("Frente a la comparación", class_name="tp-etiqueta", style={"line-height": "1.2"}),
        rx.foreach(
            EstadoApp.columnas_config,
            lambda col: rx.el.div(
                rx.el.span(rx.match(col.diferencia, *TEXTO_DIFERENCIA, "")),
                class_name="tp-conector",
                data_diferencia=col.diferencia,
                data_col=estado_paso(col.indice, paso),
            ),
        ),
        class_name="tabla-pasos",
        style={"--columnas": EstadoApp.total_pasos},
        aria_label="Pasos donde tu configuración evita un fallo o hace uno de más",
    )


def tablas() -> rx.Component:
    """Las dos tablas conectadas y el botón de exportar."""
    return rx.el.section(
        rx.el.h2("Tabla paso a paso", style={"margin-bottom": "var(--e-3)"}),
        rx.el.div(
            _tabla("Tu configuración", EstadoApp.descripcion, EstadoApp.columnas_config),
            _conectores(),
            _tabla(EstadoApp.nombre_comparacion, "algoritmo de comparación", EstadoApp.columnas_comparacion),
            class_name="tablas-cinta",
            style={"--escala": EstadoApp.escala},
        ),
        rx.el.div(
            rx.el.div(
                rx.el.span("Debajo de cada número: historia H y contador C (B es el bit de uso, * el puntero)."),
                rx.el.span("Subrayado: acierto. Recuadro: página que entró."),
                class_name="leyenda",
            ),
            boton_icono("download", "Exportar tabla a CSV", EstadoApp.exportar_csv, ocultar_texto_en_movil=False),
            class_name="tablas-pie",
        ),
        class_name="lab-tablas",
    )
