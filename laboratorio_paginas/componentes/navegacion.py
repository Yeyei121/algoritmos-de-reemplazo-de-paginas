"""Barra superior con las secciones de la app."""

from __future__ import annotations

import reflex as rx

SECCIONES: tuple[tuple[str, str], ...] = (
    ("/", "Inicio"),
    ("/laboratorio", "Laboratorio"),
    ("/explorador", "Explorador"),
    ("/marcos", "Marcos"),
    ("/validacion", "Validación"),
)


def barra(ruta_actual: str) -> rx.Component:
    """Encabezado con la marca y los enlaces; la sección actual lleva aria-current."""
    return rx.el.header(
        rx.el.a(
            rx.el.span(class_name="marca-chip", aria_hidden="true"),
            "Laboratorio de páginas",
            href="/",
            class_name="marca",
        ),
        rx.el.nav(
            *[
                rx.el.a(
                    texto,
                    href=ruta,
                    aria_current="page" if ruta == ruta_actual else None,
                )
                for ruta, texto in SECCIONES
            ],
            class_name="navegacion",
            aria_label="Secciones",
        ),
        class_name="barra",
    )


def pie() -> rx.Component:
    """Pie de página con el contexto del trabajo."""
    return rx.el.footer(
        rx.el.p(
            "Trabajo de memoria virtual: FIFO con bits adicionales de referencia. "
            "Ingeniería de Sistemas y Computación, Universidad Tecnológica de Pereira."
        ),
        class_name="pie",
    )


def marco_pagina(ruta: str, *hijos: rx.Component) -> rx.Component:
    """Estructura común de todas las pantallas."""
    return rx.el.div(
        barra(ruta),
        rx.el.main(*hijos, class_name="pagina", id="contenido"),
        pie(),
    )
