"""Piezas pequeñas que se repiten: segmentos, botones con ícono e insignias."""

from __future__ import annotations

from collections.abc import Callable, Sequence

import reflex as rx

TAMANO_ICONO = 16


def segmentos(
    nombre: str,
    opciones: Sequence[tuple[str, str]],
    valor: rx.Var,
    al_cambiar: Callable[..., rx.event.EventSpec] | rx.EventHandler,
    etiqueta: str,
) -> rx.Component:
    """Grupo de radios con aspecto de interruptor DIP (accesible con teclado)."""
    return rx.el.div(
        *[
            rx.el.label(
                rx.el.input(
                    type="radio",
                    name=nombre,
                    value=clave,
                    checked=valor == clave,
                    on_change=al_cambiar,
                ),
                rx.el.span(texto),
            )
            for clave, texto in opciones
        ],
        class_name="segmentos",
        role="radiogroup",
        aria_label=etiqueta,
    )


def campo(titulo: str, *hijos: rx.Component, id_titulo: str | None = None) -> rx.Component:
    """Un control con su título."""
    return rx.el.div(
        rx.el.span(titulo, class_name="campo-titulo", id=id_titulo),
        *hijos,
        class_name="campo",
    )


def boton_icono(
    icono: str,
    texto: str | rx.Var,
    al_hacer_clic: rx.EventHandler | rx.event.EventSpec,
    id_boton: str | None = None,
    ocultar_texto_en_movil: bool = True,
    principal: bool = False,
    deshabilitado: rx.Var | bool = False,
) -> rx.Component:
    """Botón con ícono y texto; en celular el texto queda solo para lectores de pantalla."""
    clase_texto = "texto-control" if ocultar_texto_en_movil else ""
    return rx.el.button(
        rx.icon(icono, size=TAMANO_ICONO, aria_hidden="true"),
        rx.el.span(texto, class_name=clase_texto),
        on_click=al_hacer_clic,
        id=id_boton,
        type="button",
        title=texto,
        aria_label=texto,
        disabled=deshabilitado,
        class_name="boton boton-principal" if principal else "boton",
    )


def insignia(tipo: rx.Var | str, texto: rx.Var | str) -> rx.Component:
    """Acierto (círculo), fallo (cuadrado) o neutro; siempre con texto."""
    return rx.el.span(texto, class_name="insignia", data_tipo=tipo)
