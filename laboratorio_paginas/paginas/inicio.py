"""Portada: la carrera en vivo es el hero."""

from __future__ import annotations

import reflex as rx

from laboratorio_paginas.componentes.bus import cinta
from laboratorio_paginas.componentes.marcador import marcador
from laboratorio_paginas.componentes.navegacion import marco_pagina
from laboratorio_paginas.componentes.placa import OpcionesPlaca, placa
from laboratorio_paginas.core import presets
from laboratorio_paginas.estado.inicio import MARCOS_DEMO, InicioEstado

RUTA = "/"
ESCALA_DEMO = "0.75"


def _carrera() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                marcador("FIFO", InicioEstado.digitos_fifo, "fallo"),
                marcador("FIFO con bits", InicioEstado.digitos_propuesta, "led"),
                class_name="marcadores",
                style={"max-width": "320px"},
            ),
            rx.el.button(
                rx.cond(InicioEstado.demo_corriendo, "Pausar demo", "Reproducir demo"),
                type="button",
                class_name="boton",
                on_click=InicioEstado.alternar_demo,
            ),
            class_name="config-fila",
            style={"justify-content": "space-between", "align-items": "flex-end"},
        ),
        rx.el.div(
            cinta(InicioEstado.referencias_demo, InicioEstado.demo_paso, interactiva=False),
            class_name="bus",
            style={"--escala": ESCALA_DEMO, "display": "block", "padding": "var(--e-1) var(--e-3)"},
        ),
        rx.el.div(
            placa(
                InicioEstado.demo_fifo,
                "FIFO",
                "como en el Excel",
                MARCOS_DEMO,
                ESCALA_DEMO,
                OpcionesPlaca(compacta=True, es_base=True, modo_base="fifo"),
            ),
            placa(
                InicioEstado.demo_propuesta,
                "FIFO con bits",
                "historia, uso y envejecimiento",
                MARCOS_DEMO,
                ESCALA_DEMO,
                OpcionesPlaca(compacta=True),
                k=presets.PROPUESTA.config.historia,
            ),
            class_name="carrera-placas",
        ),
        class_name="carrera",
        aria_label="Demo: FIFO contra FIFO con bits en la secuencia del profesor con 3 marcos",
    )


def _accesos() -> rx.Component:
    accesos = (
        ("/laboratorio", "Laboratorio", "Arma tu combinación de bits y mira el paso a paso contra el original."),
        ("/explorador", "Explorador", "Todas las combinaciones en tu secuencia, con ranking y mapa de calor."),
        ("/marcos", "Gráfica por marcos", "De 1 a 10 marcos, con la anomalía de Belady marcada."),
        ("/validacion", "Validación", "Por qué la configuración recomendada no está hecha a la medida."),
    )
    return rx.el.ul(
        *[rx.el.li(rx.el.a(titulo, href=ruta), rx.el.p(texto)) for ruta, titulo, texto in accesos],
        class_name="accesos",
    )


def _explicacion() -> rx.Component:
    bloques = (
        (
            "El problema",
            "Cuando la memoria está llena y se pide una página que no está, hay que sacar otra. "
            "FIFO saca la que entró primero, aunque se esté usando todo el tiempo.",
        ),
        (
            "Los bits",
            "A cada marco le agregamos un registro de historia (si se usó en las últimas iteraciones), "
            "un contador de usos que envejece y, si se quiere, bits de modificada y de fijada.",
        ),
        (
            "La regla de salida",
            "Primero salen las que no se usaron en la ventana, luego las menos usadas, luego la de "
            "historia más baja y, si siguen empatadas, la más antigua, como en FIFO.",
        ),
    )
    return rx.el.div(
        *[rx.el.div(rx.el.h3(titulo), rx.el.p(texto)) for titulo, texto in bloques],
        class_name="explicacion",
    )


def pagina() -> rx.Component:
    """Portada."""
    return marco_pagina(
        RUTA,
        rx.el.section(
            rx.el.div(
                rx.el.h1("FIFO con memoria de lo que pasó"),
                rx.el.p(
                    "El profesor le puso un bit de uso a FIFO y siguió en 12 fallos. Con historia, "
                    "contador y envejecimiento, la misma secuencia baja a 9. Mira la carrera."
                ),
                rx.el.div(
                    rx.el.a("Abrir el laboratorio", href="/laboratorio", class_name="boton boton-principal"),
                    rx.el.a("Ver la validación", href="/validacion", class_name="boton"),
                    class_name="portada-acciones",
                ),
            ),
            _carrera(),
            class_name="portada",
        ),
        rx.el.section(_explicacion(), class_name="seccion", style={"margin-top": "var(--e-5)"}),
        rx.el.section(rx.el.h2("Secciones"), _accesos(), class_name="seccion"),
    )
