"""Resumen final del laboratorio."""

from __future__ import annotations

import reflex as rx

from laboratorio_paginas.estado.app import EstadoApp


def _dato(titulo: str | rx.Var, *valor: rx.Component | rx.Var | str) -> rx.Component:
    return rx.el.div(rx.el.dt(titulo), rx.el.dd(*valor))


def resumen() -> rx.Component:
    """Fallos, porcentaje, aciertos y diferencias contra la comparación y el Óptimo."""
    r = EstadoApp.resumen
    return rx.el.section(
        rx.el.h2("Resumen al final de la secuencia", style={"margin-bottom": "var(--e-3)"}),
        rx.el.dl(
            _dato("Fallos", r.fallos, rx.el.small(" de ", r.total)),
            _dato("Porcentaje de fallos", r.tasa),
            _dato("Aciertos", r.aciertos),
            _dato(
                rx.el.span("Frente a ", r.nombre_comparacion),
                r.diferencia_comparacion,
                rx.el.small(" (", r.fallos_comparacion, ")"),
            ),
            _dato("Frente al Óptimo", r.diferencia_optimo, rx.el.small(" (", r.fallos_optimo, ")")),
            _dato("Fallos evitados", r.evitados, rx.el.small(" y ", r.perdidos, " de más")),
            rx.cond(
                EstadoApp.usa_m | EstadoApp.tiene_escrituras,
                _dato(
                    "Escrituras a disco",
                    r.escrituras,
                    rx.el.small(" (", r.nombre_comparacion, ": ", r.escrituras_comparacion, ")"),
                ),
            ),
            class_name="resumen",
        ),
        rx.el.p(r.veredicto, class_name="veredicto"),
        class_name="lab-resumen",
    )
