"""Cálculos cacheados que consume la interfaz.

Se calculan una vez por secuencia, marcos y configuración; la interfaz solo
cambia el índice del paso.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from laboratorio_paginas.core.algoritmos import BASES, FifoBits
from laboratorio_paginas.core.explorador import Exploracion, explorar
from laboratorio_paginas.core.metricas import MARCOS_CURVA, curva
from laboratorio_paginas.core.modelos import ConfigBits, Resultado
from laboratorio_paginas.core.secuencias import Secuencia, parsear
from laboratorio_paginas.estado import vistas

TAMANO_CACHE = 256


@lru_cache(maxsize=TAMANO_CACHE)
def secuencia(texto: str) -> Secuencia:
    """Secuencia ya validada a partir de su texto normalizado."""
    return parsear(texto)


@lru_cache(maxsize=TAMANO_CACHE)
def simular_bits(texto: str, marcos: int, config: ConfigBits) -> Resultado:
    """FIFO con bits, con todas sus instantáneas."""
    return FifoBits(config).simular(secuencia(texto), marcos)


@lru_cache(maxsize=TAMANO_CACHE)
def simular_base(clave: str, texto: str, marcos: int) -> Resultado:
    """Un algoritmo base (fifo, segunda, lru, mru, optimo)."""
    return BASES[clave].simular(secuencia(texto), marcos)


@lru_cache(maxsize=TAMANO_CACHE)
def exploracion(texto: str, marcos: int) -> Exploracion:
    """Todas las combinaciones del espacio en la secuencia."""
    return explorar(secuencia(texto), marcos)


@dataclass(frozen=True)
class Curvas:
    """Fallos de 1 a 10 marcos para cada línea de la gráfica."""

    fifo: tuple[int, ...]
    config: tuple[int, ...]
    optimo: tuple[int, ...]
    lru: tuple[int, ...]
    segunda: tuple[int, ...]


@lru_cache(maxsize=TAMANO_CACHE)
def curvas(texto: str, config: ConfigBits) -> Curvas:
    """Curvas por número de marcos para la gráfica."""
    sec = secuencia(texto)
    return Curvas(
        fifo=curva(BASES["fifo"], sec),
        config=curva(FifoBits(config), sec),
        optimo=curva(BASES["optimo"], sec),
        lru=curva(BASES["lru"], sec),
        segunda=curva(BASES["segunda"], sec),
    )


def mejores_por_marcos(texto: str) -> tuple[Exploracion, ...]:
    """La exploración completa para cada número de marcos de la gráfica."""
    return tuple(exploracion(texto, n) for n in MARCOS_CURVA)


@lru_cache(maxsize=TAMANO_CACHE)
def vistas_bits(texto: str, marcos: int, config: ConfigBits) -> tuple[vistas.PasoVista, ...]:
    """Instantáneas de la configuración ya traducidas para la placa."""
    return tuple(vistas.pasos_vista(simular_bits(texto, marcos, config), config))


@lru_cache(maxsize=TAMANO_CACHE)
def vistas_base(clave: str, texto: str, marcos: int) -> tuple[vistas.PasoVista, ...]:
    """Instantáneas de un algoritmo base ya traducidas para la placa compacta."""
    return tuple(vistas.pasos_vista(simular_base(clave, texto, marcos), None))
