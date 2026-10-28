"""Estado de la gráfica de fallos por número de marcos."""

from __future__ import annotations

import dataclasses

import reflex as rx

from laboratorio_paginas.core.metricas import MARCOS_CURVA, puntos_belady
from laboratorio_paginas.estado import calculos
from laboratorio_paginas.estado.app import DEPS_CONFIG, DEPS_SECUENCIA, EstadoApp


@dataclasses.dataclass
class FilaMarcos:
    """Una fila de la tabla debajo de la gráfica."""

    marcos: int = 0
    fifo: int = 0
    config: int = 0
    optimo: int = 0
    lru: int = 0
    segunda: int = 0
    diferencia: str = ""
    gana: bool = False
    pierde: bool = False
    belady_fifo: bool = False
    belady_config: bool = False
    mejor_descripcion: str = ""
    mejor_fallos: int = 0


class MarcosEstado(EstadoApp):
    """Curvas de 1 a 10 marcos para FIFO, la configuración, el Óptimo, LRU y 2.ª oportunidad."""

    mostrar_lru: bool = False
    mostrar_segunda: bool = False

    @rx.var(deps=DEPS_CONFIG, auto_deps=False)
    def datos(self) -> list[dict[str, int | None]]:
        """Filas para recharts; los puntos de Belady van en sus propias claves."""
        curvas = calculos.curvas(self.texto, self._config())
        belady_fifo = set(puntos_belady(curvas.fifo))
        belady_config = set(puntos_belady(curvas.config))
        filas: list[dict[str, int | None]] = []
        for i, n in enumerate(MARCOS_CURVA):
            filas.append(
                {
                    "marcos": n,
                    "fifo": curvas.fifo[i],
                    "config": curvas.config[i],
                    "optimo": curvas.optimo[i],
                    "lru": curvas.lru[i],
                    "segunda": curvas.segunda[i],
                    "belady_fifo": curvas.fifo[i] if n in belady_fifo else None,
                    "belady_config": curvas.config[i] if n in belady_config else None,
                }
            )
        return filas

    @rx.var(deps=DEPS_CONFIG, auto_deps=False)
    def tabla(self) -> list[FilaMarcos]:
        """Valores de la gráfica y la mejor combinación del explorador para cada n."""
        from laboratorio_paginas.estado.vistas import con_signo

        curvas = calculos.curvas(self.texto, self._config())
        belady_fifo = set(puntos_belady(curvas.fifo))
        belady_config = set(puntos_belady(curvas.config))
        exploraciones = calculos.mejores_por_marcos(self.texto)
        filas: list[FilaMarcos] = []
        for i, n in enumerate(MARCOS_CURVA):
            diferencia = curvas.config[i] - curvas.fifo[i]
            mejor = exploraciones[i].mejor
            filas.append(
                FilaMarcos(
                    marcos=n,
                    fifo=curvas.fifo[i],
                    config=curvas.config[i],
                    optimo=curvas.optimo[i],
                    lru=curvas.lru[i],
                    segunda=curvas.segunda[i],
                    diferencia=con_signo(diferencia),
                    gana=diferencia < 0,
                    pierde=diferencia > 0,
                    belady_fifo=n in belady_fifo,
                    belady_config=n in belady_config,
                    mejor_descripcion=mejor.config.describir(),
                    mejor_fallos=mejor.fallos,
                )
            )
        return filas

    @rx.var(deps=DEPS_SECUENCIA, auto_deps=False)
    def hay_belady(self) -> bool:
        """True si FIFO muestra la anomalía en esta secuencia."""
        return bool(puntos_belady(calculos.curvas(self.texto, self._config()).fifo))

    @rx.event
    def alternar_lru(self, valor: bool) -> None:
        """Muestra u oculta la línea de LRU."""
        self.mostrar_lru = valor

    @rx.event
    def alternar_segunda(self, valor: bool) -> None:
        """Muestra u oculta la línea de segunda oportunidad."""
        self.mostrar_segunda = valor
