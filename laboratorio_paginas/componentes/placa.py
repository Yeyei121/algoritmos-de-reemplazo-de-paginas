"""La placa de memoria: zócalos (marcos), chips (páginas), LEDs (bits) y disco.

Este módulo solo pinta la instantánea del paso; el movimiento vive en
assets/animaciones.css y se dispara porque los zócalos cambian de `key` en cada paso.
"""

from __future__ import annotations

from dataclasses import dataclass

import reflex as rx

from laboratorio_paginas.estado.vistas import ChipVista, PasoVista

EVENTO_ACIERTO = "acierto"
EVENTO_NINGUNO = "ninguno"


@dataclass(frozen=True)
class OpcionesPlaca:
    """Qué muestra cada chip según el algoritmo de la placa."""

    compacta: bool = False
    mostrar_m: rx.Var | bool = False
    mostrar_p: rx.Var | bool = False
    es_base: bool = False
    """True en placas de algoritmos base (sin bits extra)."""
    modo_base: rx.Var | str = "fifo"
    """En placas base: «fifo», «lru» o «segunda», para el dato pequeño de cada chip."""


def _registro_h(chip: ChipVista) -> rx.Component:
    return rx.el.div(
        rx.el.span("H", class_name="etiqueta-bits", aria_hidden="true"),
        rx.el.span(
            rx.foreach(chip.leds, lambda bit: rx.el.span(class_name="led", data_on=bit)),
            rx.el.span(class_name="led led-caido", data_on=chip.led_caido),
            class_name="registro-leds",
            aria_hidden="true",
        ),
        rx.el.span(
            rx.el.span(chip.historia_previa, class_name="bits-antes", aria_hidden="true"),
            rx.el.span(chip.historia, class_name="bits-despues"),
            class_name="bits-texto",
            aria_label="Historia " + chip.historia,
        ),
        class_name="fila-bits",
    )


def _contador(chip: ChipVista) -> rx.Component:
    return rx.el.div(
        rx.el.span("C", class_name="etiqueta-bits", aria_hidden="true"),
        rx.el.span(
            rx.foreach(chip.puntos, lambda estado: rx.el.span(class_name="punto", data_estado=estado)),
            class_name="puntos",
            role="img",
            aria_label="Contador " + chip.contador.to_string(),
        ),
        class_name="fila-bits",
    )


def _banderas(chip: ChipVista, opciones: OpcionesPlaca) -> rx.Component:
    return rx.el.div(
        rx.cond(opciones.mostrar_m, rx.el.span("M", class_name="bandera", data_on=chip.modificada, title="Modificada")),
        rx.cond(opciones.mostrar_p, rx.el.span("P", class_name="bandera", data_on=chip.fijada, title="Fijada")),
        class_name="banderas",
    )


def _dato_base(chip: ChipVista, opciones: OpcionesPlaca) -> rx.Component:
    """Lo que decide cada algoritmo base: llegada (FIFO), último uso (LRU) o bit R (2.ª op.)."""
    return rx.match(
        opciones.modo_base,
        (
            "segunda",
            rx.el.div(
                rx.el.div(
                    rx.el.span("R", class_name="etiqueta-bits", aria_hidden="true"),
                    rx.el.span(rx.el.span(class_name="led", data_on=chip.bit_r), class_name="registro-leds"),
                    rx.el.span(chip.bit_r, class_name="bits-texto", aria_label="Bit R " + chip.bit_r),
                    class_name="fila-bits",
                ),
                rx.cond(chip.puntero, rx.el.span("puntero", class_name="puntero-marca")),
            ),
        ),
        ("lru", rx.el.span("usada en ", chip.ultimo_uso, class_name="chip-dato")),
        rx.el.span("entró en ", chip.llegada, class_name="chip-dato"),
    )


def _sello(chip: ChipVista) -> rx.Component:
    return rx.cond(
        chip.evento == EVENTO_ACIERTO,
        rx.el.span("Acierto", class_name="sello", data_tipo="acierto"),
        rx.cond(chip.evento != EVENTO_NINGUNO, rx.el.span("Fallo", class_name="sello", data_tipo="fallo")),
    )


def _chip(chip: ChipVista, paso: PasoVista, opciones: OpcionesPlaca) -> rx.Component:
    if opciones.es_base:
        cuerpo = [_dato_base(chip, opciones)]
    else:
        cuerpo = [
            rx.cond(chip.leds.length() > 0, _registro_h(chip)),
            rx.cond(chip.puntos.length() > 0, _contador(chip)),
            _banderas(chip, opciones),
            rx.cond(
                paso.envejecimiento & (chip.puntos.length() > 0),
                rx.el.span("÷2", class_name="division", title="Envejecimiento: C se divide entre 2"),
            ),
        ]
    return rx.el.div(
        rx.el.span(class_name="chip-muesca", aria_hidden="true"),
        rx.el.span(chip.pagina, class_name="chip-pagina"),
        *cuerpo,
        _sello(chip),
        class_name="chip",
        data_evento=chip.evento,
        data_candidata=chip.candidata,
        aria_label="Página " + chip.pagina,
    )


def _fantasma(chip: ChipVista) -> rx.Component:
    """La víctima: se levanta del zócalo y baja por la pista hasta el disco."""
    return rx.el.div(
        rx.el.span(class_name="chip-muesca"),
        rx.el.span(chip.salio, class_name="chip-pagina"),
        class_name="chip chip-fantasma",
        aria_hidden="true",
    )


def _zocalo(chip: ChipVista, paso: PasoVista, opciones: OpcionesPlaca) -> rx.Component:
    return rx.el.div(
        rx.el.span(class_name="pista pista-entrada", aria_hidden="true"),
        rx.el.div(
            rx.cond(chip.libre, rx.el.span("libre", class_name="zocalo-vacio"), _chip(chip, paso, opciones)),
            rx.cond(chip.salio != "", _fantasma(chip)),
            class_name="zocalo-marco",
        ),
        rx.el.span(class_name="pista pista-salida", aria_hidden="true"),
        rx.el.span(chip.designador, class_name="designador"),
        class_name="zocalo",
        data_referenciado=chip.evento != EVENTO_NINGUNO,
        style={"--i": chip.marco},
    )


def _disco(paso: PasoVista) -> rx.Component:
    return rx.el.div(
        rx.el.span(class_name="disco-dedos", aria_hidden="true"),
        rx.el.span(rx.el.strong("Disco"), " (memoria virtual)", class_name="disco-texto"),
        rx.cond(
            paso.escritura_disco,
            rx.el.span(
                "Escritura a disco: la ",
                paso.victima,
                " estaba modificada",
                class_name="disco-escritura",
                key=paso.indice.to_string() + "w",
            ),
        ),
        class_name="disco",
    )


def placa(
    paso: PasoVista,
    titulo: rx.Var | str,
    detalle: rx.Var | str,
    marcos: rx.Var | int,
    escala: rx.Var | str,
    opciones: OpcionesPlaca,
    k: rx.Var | int = 0,
) -> rx.Component:
    """Placa completa del paso actual."""
    return rx.el.section(
        rx.el.div(
            rx.el.h2(titulo) if not opciones.compacta else rx.el.h3(titulo),
            rx.el.small(detalle),
            class_name="placa-cabecera",
        ),
        rx.el.div(
            rx.foreach(paso.chips, lambda chip: _zocalo(chip, paso, opciones)),
            class_name="zocalos",
            key=paso.indice.to_string(),
        ),
        rx.el.div(class_name="cobre-bus", aria_hidden="true"),
        _disco(paso),
        rx.cond(
            paso.envejecimiento, rx.el.div(class_name="onda", aria_hidden="true", key=paso.indice.to_string() + "o")
        ),
        class_name="placa",
        data_compacta="true" if opciones.compacta else "false",
        style={"--n": marcos, "--k": k, "--escala": escala},
        aria_label=titulo,
    )
