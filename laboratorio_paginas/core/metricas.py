"""Métricas para comparar algoritmos: resumen, pasos evitados y curva por marcos."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from laboratorio_paginas.core.algoritmos.base import Algoritmo
from laboratorio_paginas.core.modelos import Resultado
from laboratorio_paginas.core.secuencias import Secuencia

MARCOS_CURVA = range(1, 11)


class Diferencia(StrEnum):
    """Cómo le fue a la configuración frente a la comparación en un paso."""

    IGUAL = "igual"
    EVITADO = "evitado"
    """La comparación falla y la configuración no."""
    PERDIDO = "perdido"
    """La configuración falla y la comparación no."""


def diferencias(propio: Resultado, comparacion: Resultado) -> tuple[Diferencia, ...]:
    """Paso a paso: dónde se evitó un fallo y dónde se perdió uno."""
    salida: list[Diferencia] = []
    for a, b in zip(propio.pasos, comparacion.pasos, strict=True):
        if a.acierto and b.fallo:
            salida.append(Diferencia.EVITADO)
        elif a.fallo and b.acierto:
            salida.append(Diferencia.PERDIDO)
        else:
            salida.append(Diferencia.IGUAL)
    return tuple(salida)


@dataclass(frozen=True)
class Resumen:
    """Números finales para el panel de resumen."""

    fallos: int
    aciertos: int
    tasa: float
    diferencia_comparacion: int
    diferencia_optimo: int
    escrituras: int
    evitados: int
    perdidos: int


def resumir(propio: Resultado, comparacion: Resultado, optimo: Resultado) -> Resumen:
    """Resumen de la configuración contra la comparación y el Óptimo."""
    cambios = diferencias(propio, comparacion)
    return Resumen(
        fallos=propio.fallos,
        aciertos=propio.aciertos,
        tasa=propio.tasa_fallos,
        diferencia_comparacion=propio.fallos - comparacion.fallos,
        diferencia_optimo=propio.fallos - optimo.fallos,
        escrituras=propio.escrituras_disco,
        evitados=cambios.count(Diferencia.EVITADO),
        perdidos=cambios.count(Diferencia.PERDIDO),
    )


def curva(algoritmo: Algoritmo, secuencia: Secuencia, marcos: range = MARCOS_CURVA) -> tuple[int, ...]:
    """Fallos para cada número de marcos."""
    return tuple(algoritmo.simular(secuencia, n).fallos for n in marcos)


def puntos_belady(valores: tuple[int, ...], marcos: range = MARCOS_CURVA) -> tuple[int, ...]:
    """Números de marcos donde hay anomalía de Belady (más marcos, más fallos)."""
    return tuple(marcos[i] for i in range(1, len(valores)) if valores[i] > valores[i - 1])
