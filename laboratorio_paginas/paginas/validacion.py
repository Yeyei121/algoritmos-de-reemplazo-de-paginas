"""Pantalla de validación: entrenamiento, prueba y casos donde la mejora no gana.

Los datos no dependen del usuario, así que se leen una vez al compilar la página.
"""

from __future__ import annotations

import reflex as rx

from laboratorio_paginas.componentes.navegacion import marco_pagina
from laboratorio_paginas.core import validacion
from laboratorio_paginas.core.modelos import ConfigBits
from laboratorio_paginas.core.secuencias import LONGITUD_GENERADA, PAGINAS_GENERADOR
from laboratorio_paginas.estado.app import EstadoApp
from laboratorio_paginas.estado.vistas import decimal

RUTA = "/validacion"
NOMBRE_RECOMENDADA = validacion.NOMBRE_RECOMENDADA
ORDEN_COLUMNAS = ("Óptimo", NOMBRE_RECOMENDADA, "LRU", "2.ª oportunidad", "FIFO")
TIPOS_BARRA = {"Óptimo": "optimo", NOMBRE_RECOMENDADA: "recomendada"}


def _boton_cargar(config: ConfigBits, texto: str = "Cargar en el laboratorio") -> rx.Component:
    return rx.el.button(
        texto,
        type="button",
        class_name="boton",
        on_click=EstadoApp.cargar_en_laboratorio(
            config.historia, config.contador, config.envejecimiento, config.orden.value
        ),
    )


def _barras(fila: validacion.ResultadoMarcos) -> rx.Component:
    promedios = sorted(fila.promedios_prueba.items(), key=lambda par: par[1])
    maximo = max(v for _, v in promedios)
    return rx.el.div(
        rx.el.h3(f"{fila.marcos} marcos"),
        rx.el.div(
            *[
                rx.el.div(
                    rx.el.span(nombre),
                    rx.el.span(
                        rx.el.span(class_name="barra-relleno", style={"width": f"{100 * valor / maximo:.1f}%"}),
                        class_name="barra-pista",
                        aria_hidden="true",
                    ),
                    rx.el.span(decimal(valor), class_name="num"),
                    class_name="barra-fila",
                    data_tipo=TIPOS_BARRA.get(nombre, ""),
                )
                for nombre, valor in promedios
            ],
            class_name="barras",
            role="list",
            aria_label=f"Promedio de fallos en prueba con {fila.marcos} marcos",
        ),
        rx.el.p(
            _ventaja(fila),
            style={"font-size": "var(--t-16)"},
        ),
        rx.el.p(
            f"Fallos totales de la recomendada en entrenamiento: {fila.entrenamiento_recomendada}.",
            class_name="tenue",
            style={"margin-top": "var(--e-2)", "font-size": "var(--t-14)"},
        ),
        style={"display": "grid", "gap": "var(--e-3)"},
    )


def _ventaja(fila: validacion.ResultadoMarcos) -> str:
    """«0,86 fallos menos por secuencia que FIFO (5,1 %)»."""
    fifo = fila.promedios_prueba["FIFO"]
    propia = fila.promedios_prueba[NOMBRE_RECOMENDADA]
    menos = fifo - propia
    return (
        f"La recomendada hace {decimal(menos)} fallos menos por secuencia que FIFO "
        f"({decimal(100 * menos / fifo, 1)} % menos)."
    )


def _celda_clasica(fallos: dict[str, int], nombre: str) -> rx.Component:
    valor = fallos[nombre]
    if nombre != NOMBRE_RECOMENDADA:
        return rx.el.td(valor, class_name="num")
    fifo = fallos["FIFO"]
    if valor < fifo:
        contenido: rx.Component | int = rx.el.span(valor, class_name="mejor", title="Gana a FIFO")
    elif valor > fifo:
        contenido = rx.el.span(valor, class_name="peor", title="Pierde contra FIFO")
    else:
        contenido = valor
    return rx.el.td(contenido, class_name="num")


def _tabla_clasicas(datos: validacion.Validacion) -> rx.Component:
    return rx.el.div(
        rx.el.table(
            rx.el.thead(
                rx.el.tr(
                    rx.el.th("Secuencia"),
                    rx.el.th("Marcos", class_name="num"),
                    *[rx.el.th(nombre, class_name="num") for nombre in ORDEN_COLUMNAS],
                )
            ),
            rx.el.tbody(
                *[
                    rx.el.tr(
                        rx.el.td(fila.secuencia),
                        rx.el.td(fila.marcos, class_name="num"),
                        *[_celda_clasica(fila.fallos, nombre) for nombre in ORDEN_COLUMNAS],
                        data_destacada=fila.fallos[NOMBRE_RECOMENDADA] > fila.fallos["FIFO"],
                    )
                    for fila in datos.clasicas
                ]
            ),
            class_name="tabla",
        ),
        class_name="tabla-cinta",
    )


def _metodo() -> rx.Component:
    return rx.el.ol(
        rx.el.li(
            rx.el.strong("Generar. "),
            f"Cada semilla da {LONGITUD_GENERADA} referencias a las páginas 0 a {PAGINAS_GENERADOR - 1}. "
            "El programa trabaja sobre un grupo de 3 páginas (el 80 % de las referencias sale de ahí) y "
            "ese grupo cambia de vez en cuando, como cuando un programa pasa de una función a otra.",
        ),
        rx.el.li(
            rx.el.strong("Entrenar. "),
            "Con las semillas 1 a 500 se prueban todas las combinaciones del explorador. Gana la de menos "
            "fallos totales; si empatan, la de menos bits y luego el orden Propuesta.",
        ),
        rx.el.li(
            rx.el.strong("Probar. "),
            "La ganadora se mide con las semillas 501 a 1000, que no se usaron para elegirla. "
            "Ese promedio es el que vale.",
        ),
        class_name="pasos-metodo",
    )


def pagina() -> rx.Component:
    """Validación completa."""
    datos = validacion.obtener()
    recomendada = datos.recomendada
    tres = datos.por_marcos[0]
    prueba_recomendada = tres.promedios_prueba[NOMBRE_RECOMENDADA]
    return marco_pagina(
        RUTA,
        rx.el.div(
            rx.el.h1("Validación"),
            rx.el.p(
                "Si eligiéramos los bits mirando solo la secuencia del profesor, podríamos estar haciendo "
                "trampa sin darnos cuenta. Por eso la configuración recomendada se elige con unas "
                "secuencias y se mide con otras."
            ),
            class_name="pagina-titulo",
        ),
        rx.el.section(rx.el.h2("Cómo se hizo"), _metodo(), class_name="seccion", style={"margin-top": "0"}),
        rx.el.section(
            rx.el.h2("Configuración recomendada"),
            rx.el.div(
                rx.el.strong(recomendada.describir()),
                rx.el.p(
                    f"{recomendada.costo_bits} bits por marco. Es la misma con 3 y con 4 marcos. "
                    f"En las 500 secuencias de prueba promedia {decimal(prueba_recomendada)} fallos con 3 marcos, "
                    f"contra {decimal(tres.promedios_prueba['FIFO'])} de FIFO "
                    f"y {decimal(tres.promedios_prueba['LRU'])} de LRU, sin el costo de ordenar de LRU."
                ),
                rx.el.div(_boton_cargar(recomendada)),
                class_name="aviso",
                style={"max-width": "72ch"},
            ),
            class_name="seccion",
        ),
        rx.el.section(
            rx.el.h2("Promedio de fallos en las secuencias de prueba"),
            rx.el.p("Menos es mejor. El Óptimo es el piso: conoce el futuro y ningún sistema real lo alcanza."),
            rx.el.div(*[_barras(fila) for fila in datos.por_marcos], class_name="dos-columnas"),
            class_name="seccion",
        ),
        rx.el.section(
            rx.el.h2("Mejor para una secuencia no es mejor en general"),
            rx.el.div(
                rx.el.p(
                    "En la secuencia del profesor con 3 marcos, un contador de 1 bit con envejecimiento cada 4 "
                    f"y sin historia también da {datos.contraejemplo_profesor} fallos, con un solo bit. "
                    "Visto solo ahí parecería la mejor opción."
                ),
                rx.el.p(
                    f"Pero en las secuencias de prueba promedia {decimal(datos.contraejemplo_prueba)} fallos, "
                    f"peor que la recomendada ({decimal(prueba_recomendada)}). Le fue bien en esa secuencia, "
                    "pero un contador de 1 bit solo distingue «se volvió a usar» de «no», y eso no alcanza "
                    "en general."
                ),
                rx.el.div(
                    _boton_cargar(validacion.CONTRAEJEMPLO, "Cargar el contraejemplo en el laboratorio"),
                ),
                class_name="caso",
            ),
            class_name="seccion",
        ),
        rx.el.section(
            rx.el.h2("Dónde gana y dónde no"),
            rx.el.p(
                "La recomendada en las secuencias clásicas. Las filas resaltadas son las que pierde contra "
                "FIFO: con 2 marcos casi no hay espacio para que la historia sirva, y en la secuencia de "
                "Belady con 3 marcos FIFO tiene suerte."
            ),
            _tabla_clasicas(datos),
            class_name="seccion",
        ),
    )
