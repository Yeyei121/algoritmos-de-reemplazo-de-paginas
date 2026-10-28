"""Óptimo: sale la página que se vuelve a usar más tarde (conoce el futuro)."""

from __future__ import annotations

from dataclasses import dataclass

from laboratorio_paginas.core.algoritmos.base import Contexto, lista_paginas, simular_simple
from laboratorio_paginas.core.modelos import Resultado
from laboratorio_paginas.core.secuencias import Secuencia

NUNCA = 10**9
"""Distancia que se usa para las páginas que no vuelven a aparecer."""


def _proximo_uso(contexto: Contexto, pagina: int) -> int:
    for posicion in range(contexto.posicion + 1, len(contexto.secuencia)):
        if contexto.secuencia[posicion].pagina == pagina:
            return posicion + 1
    return NUNCA


def _elegir(contexto: Contexto) -> tuple[int, str]:
    proximos = [_proximo_uso(contexto, r.pagina) for r in contexto.ranuras if r.pagina is not None]
    lejano = max(proximos)
    marco = proximos.index(lejano)  # empate: el marco de menor índice
    pagina = contexto.ranuras[marco].pagina
    if lejano == NUNCA:
        sin_uso = [contexto.ranuras[i].pagina for i, p in enumerate(proximos) if p == NUNCA]
        if len(sin_uso) == 1:
            return marco, f"Sale la {pagina}: no se vuelve a usar."
        return marco, (
            f"Sale la {pagina}: ni {lista_paginas(sin_uso)} se vuelven a usar "  # type: ignore[arg-type]
            "y en el empate sale la del marco más bajo."
        )
    return marco, f"Sale la {pagina}: es la que se vuelve a usar más tarde (paso {lejano})."


@dataclass(frozen=True)
class Optimo:
    """Algoritmo de Belady; solo sirve como referencia del mínimo."""

    nombre: str = "Óptimo"

    def simular(self, secuencia: Secuencia, marcos: int) -> Resultado:
        """Simula el Óptimo."""
        return simular_simple(self.nombre, secuencia, marcos, _elegir)
