"""LRU: sale la página cuyo último uso es el más antiguo."""

from __future__ import annotations

from dataclasses import dataclass

from laboratorio_paginas.core.algoritmos.base import Contexto, simular_simple
from laboratorio_paginas.core.modelos import Resultado
from laboratorio_paginas.core.secuencias import Secuencia


def _elegir(contexto: Contexto) -> tuple[int, str]:
    marco = min(range(len(contexto.ranuras)), key=lambda i: contexto.ranuras[i].ultimo_uso)
    ranura = contexto.ranuras[marco]
    return marco, (
        f"Sale la {ranura.pagina}: es la que lleva más tiempo sin usarse (último uso en el paso {ranura.ultimo_uso})."
    )


@dataclass(frozen=True)
class Lru:
    """Menos recientemente usada."""

    nombre: str = "LRU"

    def simular(self, secuencia: Secuencia, marcos: int) -> Resultado:
        """Simula LRU."""
        return simular_simple(self.nombre, secuencia, marcos, _elegir)
