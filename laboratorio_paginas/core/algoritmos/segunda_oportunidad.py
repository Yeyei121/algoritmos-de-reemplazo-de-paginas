"""Segunda oportunidad, tal como la hizo el profesor: bit R y puntero circular."""

from __future__ import annotations

from dataclasses import dataclass

from laboratorio_paginas.core.algoritmos.base import (
    crear_decision_simple,
    crear_paso,
    lista_paginas,
)
from laboratorio_paginas.core.modelos import EstadoMarco, Evento, Paso, Resultado
from laboratorio_paginas.core.secuencias import Secuencia

BIT_ENCENDIDO = 1
BIT_APAGADO = 0


@dataclass
class _Marco:
    pagina: int | None = None
    bit_r: int = BIT_APAGADO
    llegada: int = 0
    modificada: bool = False


def _frase(victima: int, perdonadas: list[int]) -> str:
    if not perdonadas:
        return f"Sale la {victima}: el puntero la encontró con R = 0."
    unicas = list(dict.fromkeys(perdonadas))
    return (
        f"Sale la {victima}: el puntero le quitó la segunda oportunidad a {lista_paginas(unicas)} "
        f"(R pasó de 1 a 0) y se detuvo en la {victima} con R = 0."
    )


def _foto(
    marcos: list[_Marco], puntero: int, eventos: dict[int, Evento], salio: dict[int, int]
) -> tuple[EstadoMarco, ...]:
    return tuple(
        EstadoMarco(
            indice=i,
            pagina=m.pagina,
            modificada=m.modificada,
            llegada=m.llegada,
            bit_r=m.bit_r if m.pagina is not None else None,
            puntero=i == puntero,
            evento=eventos.get(i, Evento.NINGUNO),
            salio=salio.get(i),
        )
        for i, m in enumerate(marcos)
    )


@dataclass(frozen=True)
class SegundaOportunidad:
    """FIFO con bit de uso y puntero (versión del Excel del profesor).

    Mientras hay marcos libres el puntero se queda en el marco 1, como en la
    hoja del profesor. Es equivalente a «el puntero queda en el siguiente marco»:
    al llenar el último marco libre, el siguiente es justamente el marco 1.
    """

    nombre: str = "2.ª oportunidad"

    def simular(self, secuencia: Secuencia, marcos: int) -> Resultado:
        """Simula la segunda oportunidad."""
        memoria = [_Marco() for _ in range(marcos)]
        puntero = 0
        pasos: list[Paso] = []
        fallos = 0
        escrituras = 0
        for posicion, ref in enumerate(secuencia):
            indice = posicion + 1
            eventos: dict[int, Evento] = {}
            salio: dict[int, int] = {}
            victima: int | None = None
            decision = None
            escritura_disco = False
            marco = next((i for i, m in enumerate(memoria) if m.pagina == ref.pagina), None)
            acierto = marco is not None
            if marco is not None:
                memoria[marco].bit_r = BIT_ENCENDIDO
                memoria[marco].modificada |= ref.escritura
                eventos[marco] = Evento.ACIERTO
            else:
                fallos += 1
                marco = next((i for i, m in enumerate(memoria) if m.pagina is None), None)
                if marco is not None:
                    eventos[marco] = Evento.ENTRADA
                else:
                    perdonadas: list[int] = []
                    while memoria[puntero].bit_r == BIT_ENCENDIDO:
                        memoria[puntero].bit_r = BIT_APAGADO
                        perdonadas.append(memoria[puntero].pagina)  # type: ignore[arg-type]
                        puntero = (puntero + 1) % marcos
                    marco = puntero
                    victima = memoria[marco].pagina
                    escritura_disco = memoria[marco].modificada
                    escrituras += int(escritura_disco)
                    decision = crear_decision_simple(victima, marco, _frase(victima, perdonadas))  # type: ignore[arg-type]
                    salio[marco] = victima  # type: ignore[assignment]
                    eventos[marco] = Evento.REEMPLAZO
                    puntero = (puntero + 1) % marcos
                memoria[marco] = _Marco(ref.pagina, BIT_ENCENDIDO, indice, ref.escritura)
            pasos.append(
                crear_paso(
                    indice,
                    ref,
                    acierto,
                    _foto(memoria, puntero, eventos, salio),
                    victima,
                    marco,
                    decision,
                    fallos,
                    escritura_disco,
                    escrituras,
                )
            )
        return Resultado(self.nombre, marcos, tuple(pasos))
