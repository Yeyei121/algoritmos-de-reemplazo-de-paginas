"""FIFO: sale la página que lleva más tiempo cargada."""

from __future__ import annotations

from dataclasses import dataclass

from laboratorio_paginas.core.algoritmos.base import Contexto, simular_simple
from laboratorio_paginas.core.modelos import Resultado
from laboratorio_paginas.core.secuencias import Secuencia


def _elegir(contexto: Contexto) -> tuple[int, str]:
    marco = min(range(len(contexto.ranuras)), key=lambda i: contexto.ranuras[i].llegada)
    ranura = contexto.ranuras[marco]
    return marco, f"Sale la {ranura.pagina}: es la que lleva más tiempo en memoria (entró en el paso {ranura.llegada})."


@dataclass(frozen=True)
class Fifo:
    """Primero en entrar, primero en salir."""

    nombre: str = "FIFO"

    def simular(self, secuencia: Secuencia, marcos: int) -> Resultado:
        """Simula FIFO."""
        return simular_simple(self.nombre, secuencia, marcos, _elegir)
