"""Pantalla principal: el laboratorio."""

from __future__ import annotations

import reflex as rx

from laboratorio_paginas.componentes.bus import bus
from laboratorio_paginas.componentes.cascada import panel_decision, panel_marcadores
from laboratorio_paginas.componentes.navegacion import marco_pagina
from laboratorio_paginas.componentes.panel_config import panel_configuracion
from laboratorio_paginas.componentes.placa import OpcionesPlaca, placa
from laboratorio_paginas.componentes.resumen import resumen
from laboratorio_paginas.componentes.tabla_pasos import tablas
from laboratorio_paginas.estado.app import EstadoApp

RUTA = "/laboratorio"


def _centro() -> rx.Component:
    return rx.el.div(
        placa(
            EstadoApp.actual,
            "Tu configuración",
            EstadoApp.descripcion,
            EstadoApp.marcos,
            EstadoApp.escala,
            OpcionesPlaca(mostrar_m=EstadoApp.usa_m, mostrar_p=EstadoApp.usa_p),
            k=EstadoApp.historia,
        ),
        placa(
            EstadoApp.actual_comparacion,
            EstadoApp.nombre_comparacion,
            "algoritmo original, en la misma secuencia",
            EstadoApp.marcos,
            EstadoApp.escala,
            OpcionesPlaca(compacta=True, es_base=True, modo_base=EstadoApp.comparar),
        ),
        class_name="lab-centro",
    )


def _lado() -> rx.Component:
    return rx.el.div(
        panel_marcadores(),
        panel_decision(EstadoApp.actual, EstadoApp.actual_comparacion, EstadoApp.nombre_comparacion),
        class_name="lab-lado",
    )


def pagina() -> rx.Component:
    """Laboratorio completo."""
    return marco_pagina(
        RUTA,
        rx.el.div(
            rx.el.h1("Laboratorio"),
            rx.el.p(
                "Arma tu combinación de bits y mira, paso a paso, qué página sale y por qué. "
                "Abajo está la misma secuencia con el algoritmo original."
            ),
            class_name="pagina-titulo",
        ),
        rx.el.div(
            bus(),
            panel_configuracion(),
            _centro(),
            _lado(),
            tablas(),
            resumen(),
            class_name="lab",
        ),
    )
