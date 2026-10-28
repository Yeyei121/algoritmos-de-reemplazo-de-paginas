"""Piezas comunes de los algoritmos de reemplazo."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from laboratorio_paginas.core.modelos import (
    Decision,
    EstadoMarco,
    Evento,
    Paso,
    Referencia,
    Resultado,
)
from laboratorio_paginas.core.secuencias import Secuencia


class Algoritmo(Protocol):
    """Interfaz común: todos simulan una secuencia con n marcos."""

    @property
    def nombre(self) -> str:
        """Nombre corto para la interfaz."""
        ...

    def simular(self, secuencia: Secuencia, marcos: int) -> Resultado:
        """Simula la secuencia y devuelve todas las instantáneas."""
        ...


@dataclass
class Ranura:
    """Estado mutable de un marco mientras corre la simulación."""

    pagina: int | None = None
    llegada: int = 0
    ultimo_uso: int = 0
    modificada: bool = False


@dataclass(frozen=True)
class Contexto:
    """Lo que ve una política al elegir víctima."""

    ranuras: tuple[Ranura, ...]
    secuencia: Secuencia
    posicion: int
    """Posición (desde 0) de la referencia que causó el fallo."""


ElegirVictima = Callable[[Contexto], tuple[int, str]]
"""Devuelve el marco de la víctima y una frase que explica la elección."""


def buscar_marco(ranuras: list[Ranura], pagina: int) -> int | None:
    """Índice del marco que tiene la página, o None."""
    for indice, ranura in enumerate(ranuras):
        if ranura.pagina == pagina:
            return indice
    return None


def primer_libre(ranuras: list[Ranura]) -> int | None:
    """Índice del primer marco vacío, o None si la memoria está llena."""
    for indice, ranura in enumerate(ranuras):
        if ranura.pagina is None:
            return indice
    return None


def foto_simple(ranuras: list[Ranura], eventos: dict[int, Evento], salio: dict[int, int]) -> tuple[EstadoMarco, ...]:
    """Instantánea de los marcos para los algoritmos sin bits extra."""
    return tuple(
        EstadoMarco(
            indice=i,
            pagina=r.pagina,
            modificada=r.modificada,
            llegada=r.llegada,
            ultimo_uso=r.ultimo_uso,
            evento=eventos.get(i, Evento.NINGUNO),
            salio=salio.get(i),
        )
        for i, r in enumerate(ranuras)
    )


def lista_paginas(paginas: list[int] | tuple[int, ...]) -> str:
    """«la 2 y la 3», «la 7, la 0 y la 1»."""
    partes = [f"la {p}" for p in paginas]
    if len(partes) == 1:
        return partes[0]
    return ", ".join(partes[:-1]) + " y " + partes[-1]


def simular_simple(nombre: str, secuencia: Secuencia, marcos: int, elegir: ElegirVictima) -> Resultado:
    """Bucle común de FIFO, LRU, MRU y Óptimo; solo cambia la víctima."""
    ranuras = [Ranura() for _ in range(marcos)]
    pasos: list[Paso] = []
    fallos = 0
    escrituras = 0
    for posicion, ref in enumerate(secuencia):
        indice = posicion + 1
        eventos: dict[int, Evento] = {}
        salio: dict[int, int] = {}
        decision: Decision | None = None
        victima: int | None = None
        escritura_disco = False
        marco = buscar_marco(ranuras, ref.pagina)
        acierto = marco is not None
        if marco is not None:
            ranuras[marco].ultimo_uso = indice
            ranuras[marco].modificada |= ref.escritura
            eventos[marco] = Evento.ACIERTO
        else:
            fallos += 1
            marco = primer_libre(ranuras)
            if marco is None:
                marco, frase = elegir(Contexto(tuple(ranuras), secuencia, posicion))
                victima = ranuras[marco].pagina
                escritura_disco = ranuras[marco].modificada
                escrituras += int(escritura_disco)
                decision = crear_decision_simple(victima, marco, frase)
                salio[marco] = victima  # type: ignore[assignment]
                eventos[marco] = Evento.REEMPLAZO
            else:
                eventos[marco] = Evento.ENTRADA
            ranuras[marco] = Ranura(ref.pagina, indice, indice, ref.escritura)
        pasos.append(
            crear_paso(
                indice,
                ref,
                acierto,
                foto_simple(ranuras, eventos, salio),
                victima,
                marco,
                decision,
                fallos,
                escritura_disco,
                escrituras,
            )
        )
    return Resultado(nombre, marcos, tuple(pasos))


def crear_decision_simple(victima: int | None, marco: int, frase: str) -> Decision:
    """Decisión sin cascada: solo la frase del algoritmo base."""
    return Decision(
        victima=victima if victima is not None else -1,
        marco=marco,
        candidatas=(),
        fijadas_excluidas=(),
        pasos=(),
        regla_decisiva=None,
        frase=frase,
    )


def crear_paso(
    indice: int,
    ref: Referencia,
    acierto: bool,
    marcos: tuple[EstadoMarco, ...],
    victima: int | None,
    marco: int | None,
    decision: Decision | None,
    fallos: int,
    escritura_disco: bool,
    escrituras: int,
    envejecimiento: bool = False,
) -> Paso:
    """Arma la instantánea de un paso."""
    return Paso(
        indice=indice,
        referencia=ref,
        acierto=acierto,
        marcos=marcos,
        victima=victima,
        marco_afectado=marco,
        decision=decision,
        fallos_acumulados=fallos,
        escritura_disco=escritura_disco,
        escrituras_acumuladas=escrituras,
        envejecimiento=envejecimiento,
    )
