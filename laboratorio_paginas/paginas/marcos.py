"""Pantalla de la gráfica de fallos por número de marcos."""

from __future__ import annotations

import reflex as rx

from laboratorio_paginas.componentes.navegacion import marco_pagina
from laboratorio_paginas.componentes.panel_config import entrada_secuencia
from laboratorio_paginas.estado.marcos import FilaMarcos
from laboratorio_paginas.estado.marcos import MarcosEstado as M
from laboratorio_paginas.estilos import tema

RUTA = "/marcos"
ALTO_GRAFICA = 380
GROSOR_LINEA = 2.5
RADIO_BELADY = 7


def _linea(clave: str, nombre: str, color: str, punteada: bool = False, oculta: rx.Var | bool = False) -> rx.Component:
    return rx.recharts.line(
        data_key=clave,
        name=nombre,
        stroke=color,
        stroke_width=GROSOR_LINEA,
        stroke_dasharray="6 4" if punteada else "",
        dot={"r": 3, "fill": color, "stroke": color},
        type_="linear",
        hide=oculta,
        is_animation_active=False,
    )


def _belady(clave: str, nombre: str) -> rx.Component:
    """Solo puntos (sin línea) donde hay anomalía; los demás valores son nulos."""
    return rx.recharts.line(
        data_key=clave,
        name=nombre,
        stroke="transparent",
        stroke_width=0,
        dot={"r": RADIO_BELADY, "fill": tema.COLOR_BELADY, "stroke": "#0a2e22", "strokeWidth": 2},
        active_dot=False,
        legend_type="square",
        connect_nulls=False,
        is_animation_active=False,
    )


def _leyenda() -> rx.Component:
    """Leyenda propia: solo muestra las líneas visibles."""

    def item(nombre: str, color: str, punteada: bool = False) -> rx.Component:
        return rx.el.span(rx.el.i(data_punteada=punteada, style={"--color": color}), nombre)

    return rx.el.div(
        item("FIFO", tema.COLOR_FIFO),
        item("Tu configuración", tema.COLOR_CONFIG),
        item("Óptimo (piso)", tema.COLOR_OPTIMO, punteada=True),
        rx.cond(M.mostrar_lru, item("LRU", tema.COLOR_LRU)),
        rx.cond(M.mostrar_segunda, item("2.ª oportunidad", tema.COLOR_SEGUNDA)),
        rx.el.span(rx.el.b(), "Anomalía de Belady"),
        class_name="leyenda-grafica",
    )


def grafica() -> rx.Component:
    """Fallos de 1 a 10 marcos, con el Óptimo como piso y Belady marcado."""
    return rx.el.div(
        _leyenda(),
        rx.recharts.composed_chart(
            rx.recharts.cartesian_grid(stroke=tema.COLOR_REJILLA, stroke_dasharray="3 3", vertical=False),
            rx.recharts.x_axis(
                data_key="marcos",
                stroke=tema.COLOR_REJILLA,
                label={"value": "Marcos", "position": "insideBottom", "offset": -4, "fill": tema.COLOR_FIFO},
            ),
            rx.recharts.y_axis(
                stroke=tema.COLOR_REJILLA,
                allow_decimals=False,
                label={"value": "Fallos", "angle": -90, "position": "insideLeft", "fill": tema.COLOR_FIFO},
            ),
            rx.recharts.graphing_tooltip(
                content_style={"background": "#0f3d2e", "border": "1px solid #2c6b52"},
                label_style={"color": "#f0eee3"},
                item_style={"color": "#f0eee3"},
            ),
            _linea("fifo", "FIFO", tema.COLOR_FIFO),
            _linea("config", "Tu configuración", tema.COLOR_CONFIG),
            _linea("optimo", "Óptimo (piso)", tema.COLOR_OPTIMO, punteada=True),
            _linea("lru", "LRU", tema.COLOR_LRU, oculta=~M.mostrar_lru),
            _linea("segunda", "2.ª oportunidad", tema.COLOR_SEGUNDA, oculta=~M.mostrar_segunda),
            _belady("belady_fifo", "Belady en FIFO"),
            _belady("belady_config", "Belady en tu configuración"),
            data=M.datos,
            height=ALTO_GRAFICA,
            margin={"top": 8, "right": 24, "left": 8, "bottom": 16},
        ),
        class_name="grafica",
        role="img",
        aria_label="Gráfica de fallos según el número de marcos. Los valores están en la tabla de abajo.",
    )


def _fila(fila: FilaMarcos) -> rx.Component:
    return rx.el.tr(
        rx.el.td(fila.marcos, class_name="num"),
        rx.el.td(fila.fifo, rx.cond(fila.belady_fifo, rx.el.span(" Belady", class_name="peor")), class_name="num"),
        rx.el.td(fila.config, rx.cond(fila.belady_config, rx.el.span(" Belady", class_name="peor")), class_name="num"),
        rx.el.td(
            rx.cond(
                fila.gana,
                rx.el.span(fila.diferencia, class_name="mejor"),
                rx.cond(fila.pierde, rx.el.span(fila.diferencia, class_name="peor"), fila.diferencia),
            ),
            class_name="num",
        ),
        rx.el.td(fila.optimo, class_name="num"),
        rx.el.td(fila.lru, class_name="num"),
        rx.el.td(fila.segunda, class_name="num"),
        rx.el.td(fila.mejor_fallos, class_name="num"),
        rx.el.td(fila.mejor_descripcion),
        data_destacada=fila.marcos == M.marcos,
    )


def tabla() -> rx.Component:
    """Valores de la gráfica y la mejor combinación del explorador por número de marcos."""
    return rx.el.div(
        rx.el.table(
            rx.el.thead(
                rx.el.tr(
                    rx.el.th("Marcos", class_name="num"),
                    rx.el.th("FIFO", class_name="num"),
                    rx.el.th("Tu config.", class_name="num"),
                    rx.el.th("Diferencia", class_name="num"),
                    rx.el.th("Óptimo", class_name="num"),
                    rx.el.th("LRU", class_name="num"),
                    rx.el.th("2.ª op.", class_name="num"),
                    rx.el.th("Mejor del explorador", class_name="num"),
                    rx.el.th("Esa combinación"),
                )
            ),
            rx.el.tbody(rx.foreach(M.tabla, _fila)),
            class_name="tabla",
        ),
        class_name="tabla-cinta",
    )


def pagina() -> rx.Component:
    """Gráfica por marcos."""
    return marco_pagina(
        RUTA,
        rx.el.div(
            rx.el.h1("Fallos según el número de marcos"),
            rx.el.p(
                "Con más marcos casi siempre hay menos fallos, pero FIFO puede empeorar: es la anomalía de "
                "Belady. Aquí se ve tu configuración del laboratorio de 1 a 10 marcos.",
            ),
            class_name="pagina-titulo",
        ),
        rx.el.div(
            rx.el.div(entrada_secuencia(), class_name="zona"),
            rx.el.div(
                rx.el.div(
                    rx.el.label(
                        rx.el.input(type="checkbox", checked=M.mostrar_lru, on_change=M.alternar_lru(~M.mostrar_lru)),
                        "Mostrar LRU",
                        class_name="interruptor",
                    ),
                    rx.el.label(
                        rx.el.input(
                            type="checkbox", checked=M.mostrar_segunda, on_change=M.alternar_segunda(~M.mostrar_segunda)
                        ),
                        "Mostrar 2.ª oportunidad",
                        class_name="interruptor",
                    ),
                    rx.el.span("Tu configuración: ", rx.el.strong(M.descripcion), class_name="tenue"),
                    class_name="opciones-grafica",
                ),
                grafica(),
                rx.el.p(
                    "Los puntos rojos marcan la anomalía de Belady: con un marco más hay más fallos.",
                    class_name="tenue",
                    style={"margin-top": "var(--e-2)", "font-size": "var(--t-14)"},
                ),
            ),
            class_name="dos-columnas con-panel",
        ),
        rx.el.section(
            rx.el.h2("Valores"),
            rx.el.p(
                "La mejor combinación del explorador puede cambiar con el número de marcos. "
                "Con pocos marcos la mejora suele perder: la historia necesita espacio para servir."
            ),
            tabla(),
            class_name="seccion",
        ),
    )
