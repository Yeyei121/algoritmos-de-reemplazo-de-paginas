"""MRU: sale la página usada más recientemente."""

from __future__ import annotations

from dataclasses import dataclass

from laboratorio_paginas.core.algoritmos.base import Contexto, simular_simple
from laboratorio_paginas.core.modelos import Resultado
from laboratorio_paginas.core.secuencias import Secuencia


def _elegir(contexto: Contexto) -> tuple[int, str]:
    marco = max(range(len(contexto.ranuras)), key=lambda i: contexto.ranuras[i].ultimo_uso)
    ranura = contexto.ranuras[marco]
    return marco, (f"Sale la {ranura.pagina}: es la que se usó más recientemente (paso {ranura.ultimo_uso}).")


@dataclass(frozen=True)
class Mru:
    """Más recientemente usada."""

    nombre: str = "MRU"

    def simular(self, secuencia: Secuencia, marcos: int) -> Resultado:
        """Simula MRU."""
        return simular_simple(self.nombre, secuencia, marcos, _elegir)
