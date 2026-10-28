"""Marcador de fallos con dígitos de 7 segmentos."""

from __future__ import annotations

import reflex as rx

SEGMENTOS: tuple[str, ...] = ("a", "b", "c", "d", "e", "f", "g")


def _digito(valor: rx.Var, clave: rx.Var) -> rx.Component:
    return rx.el.span(
        *[rx.el.span(class_name=f"seg {s}") for s in SEGMENTOS],
        class_name="digito",
        data_d=valor,
        data_cambia="true",
        key=clave,
    )


def marcador(
    etiqueta: rx.Var | str, digitos: rx.Var, tono: str = "fallo", descripcion: rx.Var | str = ""
) -> rx.Component:
    """Display de dos dígitos; cada cambio hace parpadear los segmentos."""
    valor = digitos[0] + digitos[1]
    return rx.el.div(
        rx.el.span(rx.el.strong(etiqueta), " ", descripcion, class_name="marcador-etiqueta"),
        rx.el.span(
            _digito(digitos[0], valor + "d"),
            _digito(digitos[1], valor + "u"),
            class_name="display",
            data_tono=tono,
            role="img",
            aria_label=rx.Var.create(etiqueta).to_string() + ": " + valor + " fallos",
        ),
        class_name="marcador",
    )
