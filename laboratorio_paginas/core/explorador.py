"""Explorador: prueba todas las combinaciones de bits sin repetir equivalentes."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from laboratorio_paginas.core.algoritmos.fifo import Fifo
from laboratorio_paginas.core.algoritmos.fifo_bits import contar_fallos
from laboratorio_paginas.core.modelos import (
    CONTADORES_PERMITIDOS,
    ENVEJECIMIENTOS_PERMITIDOS,
    HISTORIAS_PERMITIDAS,
    ConfigBits,
    OrdenReglas,
    Regla,
)
from laboratorio_paginas.core.secuencias import Secuencia

TAMANO_RANKING = 10
ORDENES: tuple[OrdenReglas, ...] = tuple(OrdenReglas)

Firma = tuple[int, int, int, tuple[Regla, ...]]


def firma(config: ConfigBits) -> Firma:
    """Huella de comportamiento: dos configuraciones con la misma firma dan
    siempre el mismo resultado, en cualquier secuencia.

    - Sin historia (k = 0) no hay ventana ni recencia.
    - Sin regla de uso, los bits de C y el envejecimiento no influyen.
    - Ventana justo antes de recencia sobra: recencia ya se queda con las de H = 0.
    """
    reglas = list(config.reglas)
    for i in range(len(reglas) - 1):
        if reglas[i] is Regla.VENTANA and reglas[i + 1] is Regla.RECENCIA:
            del reglas[i]
            break
    usa_uso = Regla.USO in reglas
    contador = config.contador if usa_uso else 0
    envejecimiento = config.envejecimiento if usa_uso else 0
    return config.historia, contador, envejecimiento, tuple(reglas)


@lru_cache(maxsize=1)
def espacio() -> tuple[ConfigBits, ...]:
    """Todas las combinaciones k × C × envejecimiento × orden, sin duplicados.

    Se recorre de menor a mayor costo y con el orden Propuesta primero, así el
    representante de cada grupo equivalente es el más barato y preferido.
    """
    vistas: set[Firma] = set()
    unicas: list[ConfigBits] = []
    for k in HISTORIAS_PERMITIDAS:
        for c in CONTADORES_PERMITIDOS:
            for env in ENVEJECIMIENTOS_PERMITIDOS:
                for orden in ORDENES:
                    config = ConfigBits(historia=k, contador=c, envejecimiento=env, orden=orden)
                    huella = firma(config)
                    if huella not in vistas:
                        vistas.add(huella)
                        unicas.append(config)
    return tuple(unicas)


@lru_cache(maxsize=1)
def _representantes() -> dict[Firma, ConfigBits]:
    return {firma(c): c for c in espacio()}


def representante(config: ConfigBits) -> ConfigBits:
    """La configuración del espacio equivalente a `config` (sin M ni P)."""
    limpia = ConfigBits(config.historia, config.contador, config.envejecimiento, config.orden)
    return _representantes()[firma(limpia)]


def clave_orden(config: ConfigBits, fallos: int) -> tuple[int, int, int, int, int, int, int]:
    """Desempate: menos fallos, menos bits, orden Propuesta, y luego lo más simple."""
    return (
        fallos,
        config.costo_bits,
        int(config.orden is not OrdenReglas.PROPUESTA),
        config.historia,
        config.contador,
        config.envejecimiento,
        ORDENES.index(config.orden),
    )


@dataclass(frozen=True)
class Puntaje:
    """Resultado de una combinación en una secuencia."""

    config: ConfigBits
    fallos: int
    tasa: float
    diferencia_fifo: int

    @property
    def costo(self) -> int:
        """Bits por marco."""
        return self.config.costo_bits


@dataclass(frozen=True)
class Exploracion:
    """Todas las combinaciones evaluadas en una secuencia, ya ordenadas."""

    marcos: int
    fallos_fifo: int
    puntajes: tuple[Puntaje, ...]

    @property
    def mejor(self) -> Puntaje:
        """La mejor combinación para esta secuencia (viendo la secuencia completa)."""
        return self.puntajes[0]

    def ranking(self, cantidad: int = TAMANO_RANKING) -> tuple[Puntaje, ...]:
        """Las primeras `cantidad` combinaciones."""
        return self.puntajes[:cantidad]

    def fallos_de(self, config: ConfigBits) -> int:
        """Fallos de cualquier configuración del espacio, aunque sea un duplicado."""
        buscada = representante(config)
        for puntaje in self.puntajes:
            if puntaje.config == buscada:
                return puntaje.fallos
        raise KeyError(config)


def explorar(secuencia: Secuencia, marcos: int) -> Exploracion:
    """Evalúa todo el espacio en la secuencia y ordena con el desempate oficial."""
    fifo = Fifo().simular(secuencia, marcos).fallos
    total = len(secuencia)
    evaluadas = [(c, contar_fallos(c, secuencia, marcos)) for c in espacio()]
    evaluadas.sort(key=lambda par: clave_orden(par[0], par[1]))
    puntajes = tuple(
        Puntaje(config=c, fallos=f, tasa=100.0 * f / total, diferencia_fifo=f - fifo) for c, f in evaluadas
    )
    return Exploracion(marcos=marcos, fallos_fifo=fifo, puntajes=puntajes)


def mapa_calor(exploracion: Exploracion, envejecimiento: int, orden: OrdenReglas) -> list[list[int]]:
    """Matriz historia × contador con los fallos, para un envejecimiento y orden."""
    return [
        [
            exploracion.fallos_de(ConfigBits(historia=k, contador=c, envejecimiento=envejecimiento, orden=orden))
            for c in CONTADORES_PERMITIDOS
        ]
        for k in HISTORIAS_PERMITIDAS
    ]
