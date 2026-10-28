"""Configuraciones con nombre que aparecen en el laboratorio."""

from __future__ import annotations

from dataclasses import dataclass

from laboratorio_paginas.core.modelos import ConfigBits, OrdenReglas
from laboratorio_paginas.core.validacion import obtener


@dataclass(frozen=True)
class Preset:
    """Una configuración con nombre y una línea que la explica."""

    clave: str
    nombre: str
    config: ConfigBits
    descripcion: str


FIFO_PURO = Preset(
    clave="fifo_puro",
    nombre="FIFO puro",
    config=ConfigBits(historia=0, contador=0),
    descripcion="Sin bits extra. Da exactamente lo mismo que FIFO.",
)
PROPUESTA = Preset(
    clave="propuesta",
    nombre="Propuesta del grupo",
    config=ConfigBits(historia=4, contador=2, envejecimiento=8, orden=OrdenReglas.PROPUESTA),
    descripcion="Ventana de 4 iteraciones, contador de 2 bits y envejecimiento cada 8.",
)


def recomendada() -> Preset:
    """La que sale de la validación (entrenamiento con semillas 1 a 500)."""
    config = obtener().recomendada
    return Preset(
        clave="recomendada",
        nombre="Recomendada por validación",
        config=config,
        descripcion=f"La de menos fallos en 500 secuencias de entrenamiento ({config.costo_bits} bits).",
    )


def todos() -> tuple[Preset, ...]:
    """Presets en el orden del selector."""
    return (FIFO_PURO, PROPUESTA, recomendada())
