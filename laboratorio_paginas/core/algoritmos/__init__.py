"""Algoritmos de reemplazo de páginas."""

from laboratorio_paginas.core.algoritmos.base import Algoritmo
from laboratorio_paginas.core.algoritmos.fifo import Fifo
from laboratorio_paginas.core.algoritmos.fifo_bits import FifoBits, contar_fallos
from laboratorio_paginas.core.algoritmos.lru import Lru
from laboratorio_paginas.core.algoritmos.mru import Mru
from laboratorio_paginas.core.algoritmos.optimo import Optimo
from laboratorio_paginas.core.algoritmos.segunda_oportunidad import SegundaOportunidad

BASES: dict[str, Algoritmo] = {
    "fifo": Fifo(),
    "segunda": SegundaOportunidad(),
    "lru": Lru(),
    "mru": Mru(),
    "optimo": Optimo(),
}
"""Algoritmos base por clave, en el orden en que aparecen en la interfaz."""

__all__ = [
    "BASES",
    "Algoritmo",
    "Fifo",
    "FifoBits",
    "Lru",
    "Mru",
    "Optimo",
    "SegundaOportunidad",
    "contar_fallos",
]
