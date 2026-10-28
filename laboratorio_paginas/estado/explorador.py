"""Estado del explorador: ranking y mapa de calor de todas las combinaciones."""

from __future__ import annotations

import dataclasses

import reflex as rx

from laboratorio_paginas.core import presets
from laboratorio_paginas.core.explorador import Exploracion, mapa_calor, representante
from laboratorio_paginas.core.modelos import (
    CONTADORES_PERMITIDOS,
    HISTORIAS_PERMITIDAS,
    NOMBRES_ORDEN,
    ConfigBits,
    OrdenReglas,
)
from laboratorio_paginas.estado import calculos
from laboratorio_paginas.estado.app import DEPS_SECUENCIA, EstadoApp
from laboratorio_paginas.estado.vistas import con_signo, porcentaje

# Escala del mapa: más encendido = menos fallos.
COLOR_MEJOR = (0xFF, 0xB6, 0x27)
COLOR_MEDIO = (0x8A, 0x6A, 0x2A)
COLOR_PEOR = (0x18, 0x3F, 0x31)
TEXTO_CLARO = "#f0eee3"
TEXTO_OSCURO = "#0a2e22"
UMBRAL_LUMINANCIA = 0.32


@dataclasses.dataclass
class FilaRanking:
    """Una fila del ranking."""

    posicion: int = 0
    historia: int = 0
    contador: int = 0
    envejecimiento: int = 0
    orden: str = ""
    nombre_orden: str = ""
    envejecimiento_texto: str = ""
    fallos: int = 0
    tasa: str = ""
    costo: int = 0
    diferencia_fifo: str = ""
    es_recomendada: bool = False


@dataclasses.dataclass
class CeldaMapa:
    """Una celda historia × contador."""

    historia: int = 0
    contador: int = 0
    fallos: int = 0
    fondo: str = ""
    texto: str = ""
    marca: str = ""
    etiqueta: str = ""


@dataclasses.dataclass
class FilaMapa:
    """Una fila del mapa (un valor de k)."""

    etiqueta: str = ""
    celdas: list[CeldaMapa] = dataclasses.field(default_factory=list)


def _mezclar(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b, strict=True))  # type: ignore[return-value]


def _color(fallos: int, minimo: int, maximo: int) -> tuple[str, str]:
    """Fondo y color de texto de una celda según sus fallos."""
    t = 0.0 if maximo == minimo else (fallos - minimo) / (maximo - minimo)
    rgb = _mezclar(COLOR_MEJOR, COLOR_MEDIO, t * 2) if t < 0.5 else _mezclar(COLOR_MEDIO, COLOR_PEOR, (t - 0.5) * 2)
    luminancia = (0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]) / 255
    texto = TEXTO_OSCURO if luminancia > UMBRAL_LUMINANCIA else TEXTO_CLARO
    return "#{:02x}{:02x}{:02x}".format(*rgb), texto


def _texto_envejecimiento(valor: int) -> str:
    return f"cada {valor}" if valor else "apagado"


def filas_ranking(exploracion: Exploracion, recomendada: ConfigBits) -> list[FilaRanking]:
    """Las 10 mejores combinaciones como filas de tabla."""
    filas: list[FilaRanking] = []
    for i, puntaje in enumerate(exploracion.ranking(), start=1):
        config = puntaje.config
        filas.append(
            FilaRanking(
                posicion=i,
                historia=config.historia,
                contador=config.contador,
                envejecimiento=config.envejecimiento,
                orden=config.orden.value,
                nombre_orden=NOMBRES_ORDEN[config.orden],
                envejecimiento_texto=_texto_envejecimiento(config.envejecimiento),
                fallos=puntaje.fallos,
                tasa=porcentaje(puntaje.tasa),
                costo=puntaje.costo,
                diferencia_fifo=con_signo(puntaje.diferencia_fifo),
                es_recomendada=config == recomendada,
            )
        )
    return filas


def filas_mapa(exploracion: Exploracion, envejecimiento: int, orden: OrdenReglas) -> list[FilaMapa]:
    """Mapa de calor historia × contador para un envejecimiento y un orden."""
    matriz = mapa_calor(exploracion, envejecimiento, orden)
    valores = [v for fila in matriz for v in fila]
    minimo, maximo = min(valores), max(valores)
    mejor = exploracion.mejor.config
    filas: list[FilaMapa] = []
    for k, fila in zip(HISTORIAS_PERMITIDAS, matriz, strict=True):
        celdas: list[CeldaMapa] = []
        for c, fallos in zip(CONTADORES_PERMITIDOS, fila, strict=True):
            fondo, texto = _color(fallos, minimo, maximo)
            config = ConfigBits(historia=k, contador=c, envejecimiento=envejecimiento, orden=orden)
            marca = "mejor" if representante(config) == mejor else ("fifo" if k == 0 and c == 0 else "")
            celdas.append(
                CeldaMapa(
                    historia=k,
                    contador=c,
                    fallos=fallos,
                    fondo=fondo,
                    texto=texto,
                    marca=marca,
                    etiqueta={"mejor": "la mejor", "fifo": "FIFO"}.get(marca, ""),
                )
            )
        filas.append(FilaMapa(etiqueta=f"k = {k}", celdas=celdas))
    return filas


class ExploradorEstado(EstadoApp):
    """Ranking y mapa de calor de la secuencia actual."""

    env_mapa: str = "8"
    orden_mapa: str = OrdenReglas.PROPUESTA.value

    def _exploracion(self) -> Exploracion:
        return calculos.exploracion(self.texto, self.marcos)

    @rx.var(deps=DEPS_SECUENCIA, auto_deps=False)
    def ranking(self) -> list[FilaRanking]:
        """Las 10 mejores combinaciones para esta secuencia."""
        return filas_ranking(self._exploracion(), presets.recomendada().config)

    @rx.var(deps=[*DEPS_SECUENCIA, "env_mapa", "orden_mapa"], auto_deps=False)
    def mapa(self) -> list[FilaMapa]:
        """Mapa de calor historia × contador."""
        return filas_mapa(self._exploracion(), int(self.env_mapa), OrdenReglas(self.orden_mapa))

    @rx.var(deps=DEPS_SECUENCIA, auto_deps=False)
    def fallos_fifo(self) -> int:
        """Fallos de FIFO en la secuencia."""
        return self._exploracion().fallos_fifo

    @rx.var(deps=DEPS_SECUENCIA, auto_deps=False)
    def mejor_fallos(self) -> int:
        """Fallos de la mejor combinación para esta secuencia."""
        return self._exploracion().mejor.fallos

    @rx.var(deps=DEPS_SECUENCIA, auto_deps=False)
    def mejor_descripcion(self) -> str:
        """Descripción de la mejor combinación."""
        return self._exploracion().mejor.config.describir()

    @rx.var(deps=DEPS_SECUENCIA, auto_deps=False)
    def recomendada_fallos(self) -> int:
        """Fallos de la recomendada (fija) en esta secuencia."""
        return self._exploracion().fallos_de(presets.recomendada().config)

    @rx.var
    def recomendada_descripcion(self) -> str:
        """Descripción de la recomendada."""
        return presets.recomendada().config.describir()

    @rx.var(deps=DEPS_SECUENCIA, auto_deps=False)
    def combinaciones(self) -> int:
        """Combinaciones distintas que se probaron."""
        return len(self._exploracion().puntajes)

    @rx.event
    def set_env_mapa(self, valor: str) -> None:
        """Envejecimiento del mapa."""
        self.env_mapa = valor

    @rx.event
    def set_orden_mapa(self, valor: str) -> None:
        """Orden de reglas del mapa."""
        self.orden_mapa = OrdenReglas(valor).value
