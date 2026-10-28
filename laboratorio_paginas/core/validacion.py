"""Validación: elegir la configuración con unas semillas y medirla con otras.

Así la configuración recomendada no está hecha a la medida de una secuencia.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path

from laboratorio_paginas.core.algoritmos.fifo import Fifo
from laboratorio_paginas.core.algoritmos.fifo_bits import contar_fallos
from laboratorio_paginas.core.algoritmos.lru import Lru
from laboratorio_paginas.core.algoritmos.optimo import Optimo
from laboratorio_paginas.core.algoritmos.segunda_oportunidad import SegundaOportunidad
from laboratorio_paginas.core.explorador import clave_orden, espacio
from laboratorio_paginas.core.modelos import ConfigBits, OrdenReglas
from laboratorio_paginas.core.secuencias import PRECARGADAS, Secuencia, generar_con_localidad, parsear

SEMILLAS_ENTRENAMIENTO = range(1, 501)
SEMILLAS_PRUEBA = range(501, 1001)
MARCOS_VALIDADOS: tuple[int, ...] = (3, 4)
MARCOS_HONESTOS: tuple[int, ...] = (2, 3, 4)
"""Marcos para la tabla «dónde gana y dónde no», incluido 2."""

CONTRAEJEMPLO = ConfigBits(historia=0, contador=1, envejecimiento=4, orden=OrdenReglas.PROPUESTA)
"""Un solo bit que empata con la propuesta en la secuencia del profesor."""

VERSION_CACHE = 1
RUTA_CACHE = Path(__file__).resolve().parent.parent / "datos" / "validacion.json"

NOMBRE_RECOMENDADA = "Recomendada"
NOMBRE_CONTRAEJEMPLO = "Contraejemplo (1 bit)"
BASES = {"FIFO": Fifo(), "2.ª oportunidad": SegundaOportunidad(), "LRU": Lru(), "Óptimo": Optimo()}


@lru_cache(maxsize=2)
def semillas(rango: range) -> tuple[Secuencia, ...]:
    """Secuencias generadas para un rango de semillas."""
    return tuple(generar_con_localidad(s) for s in rango)


def total_fallos(config: ConfigBits, secuencias: tuple[Secuencia, ...], marcos: int) -> int:
    """Fallos de una configuración sumados sobre varias secuencias."""
    return sum(contar_fallos(config, s, marcos) for s in secuencias)


def elegir_recomendada(marcos: int) -> tuple[ConfigBits, int]:
    """Menos fallos en entrenamiento; desempate: menos bits y orden Propuesta."""
    entrenamiento = semillas(SEMILLAS_ENTRENAMIENTO)
    totales = [(c, total_fallos(c, entrenamiento, marcos)) for c in espacio()]
    mejor = min(totales, key=lambda par: clave_orden(par[0], par[1]))
    return mejor


def promedio_base(nombre: str, secuencias: tuple[Secuencia, ...], marcos: int) -> float:
    """Promedio de fallos de un algoritmo base."""
    algoritmo = BASES[nombre]
    return sum(algoritmo.simular(s, marcos).fallos for s in secuencias) / len(secuencias)


def promedio_bits(config: ConfigBits, secuencias: tuple[Secuencia, ...], marcos: int) -> float:
    """Promedio de fallos de una configuración de bits."""
    return total_fallos(config, secuencias, marcos) / len(secuencias)


@dataclass(frozen=True)
class FilaClasica:
    """Fallos en una secuencia clásica con cierto número de marcos."""

    secuencia: str
    marcos: int
    fallos: dict[str, int]


@dataclass(frozen=True)
class ResultadoMarcos:
    """Validación para un número de marcos."""

    marcos: int
    recomendada: ConfigBits
    entrenamiento_recomendada: int
    promedios_prueba: dict[str, float]


@dataclass(frozen=True)
class Validacion:
    """Todo lo que muestra la pantalla de validación."""

    por_marcos: tuple[ResultadoMarcos, ...]
    clasicas: tuple[FilaClasica, ...]
    contraejemplo_prueba: float
    contraejemplo_profesor: int

    @property
    def recomendada(self) -> ConfigBits:
        """La recomendada con 3 marcos (la que usa el resto de la app)."""
        return self.por_marcos[0].recomendada


def _validar_marcos(marcos: int) -> ResultadoMarcos:
    recomendada, total = elegir_recomendada(marcos)
    prueba = semillas(SEMILLAS_PRUEBA)
    promedios = {NOMBRE_RECOMENDADA: promedio_bits(recomendada, prueba, marcos)}
    for nombre in BASES:
        promedios[nombre] = promedio_base(nombre, prueba, marcos)
    return ResultadoMarcos(marcos, recomendada, total, promedios)


def _clasicas(recomendada: ConfigBits) -> tuple[FilaClasica, ...]:
    filas: list[FilaClasica] = []
    for item in PRECARGADAS:
        secuencia = parsear(item.texto)
        for marcos in MARCOS_HONESTOS:
            fallos = {nombre: alg.simular(secuencia, marcos).fallos for nombre, alg in BASES.items()}
            fallos[NOMBRE_RECOMENDADA] = contar_fallos(recomendada, secuencia, marcos)
            filas.append(FilaClasica(item.nombre, marcos, fallos))
    return tuple(filas)


def calcular() -> Validacion:
    """Corre toda la validación (tarda unos segundos)."""
    por_marcos = tuple(_validar_marcos(m) for m in MARCOS_VALIDADOS)
    recomendada = por_marcos[0].recomendada
    prueba = semillas(SEMILLAS_PRUEBA)
    profesor = parsear(PRECARGADAS[0].texto)
    return Validacion(
        por_marcos=por_marcos,
        clasicas=_clasicas(recomendada),
        contraejemplo_prueba=promedio_bits(CONTRAEJEMPLO, prueba, MARCOS_VALIDADOS[0]),
        contraejemplo_profesor=contar_fallos(CONTRAEJEMPLO, profesor, MARCOS_VALIDADOS[0]),
    )


# ------------------------------------------------------------------ caché


def _a_json(validacion: Validacion) -> dict[str, object]:
    datos = asdict(validacion)
    for fila in datos["por_marcos"]:
        fila["recomendada"]["orden"] = fila["recomendada"]["orden"].value
        fila["recomendada"]["paginas_fijadas"] = []
    return {"version": VERSION_CACHE, "datos": datos}


def _desde_json(contenido: dict[str, object]) -> Validacion:
    datos = contenido["datos"]
    por_marcos = tuple(
        ResultadoMarcos(
            marcos=f["marcos"],
            recomendada=ConfigBits(
                historia=f["recomendada"]["historia"],
                contador=f["recomendada"]["contador"],
                envejecimiento=f["recomendada"]["envejecimiento"],
                orden=OrdenReglas(f["recomendada"]["orden"]),
            ),
            entrenamiento_recomendada=f["entrenamiento_recomendada"],
            promedios_prueba=f["promedios_prueba"],
        )
        for f in datos["por_marcos"]  # type: ignore[index]
    )
    clasicas = tuple(FilaClasica(**f) for f in datos["clasicas"])  # type: ignore[index]
    return Validacion(
        por_marcos=por_marcos,
        clasicas=clasicas,
        contraejemplo_prueba=datos["contraejemplo_prueba"],  # type: ignore[index]
        contraejemplo_profesor=datos["contraejemplo_profesor"],  # type: ignore[index]
    )


@lru_cache(maxsize=1)
def obtener(ruta: Path = RUTA_CACHE) -> Validacion:
    """La validación desde el disco si ya se calculó; si no, la calcula y la guarda."""
    try:
        contenido = json.loads(ruta.read_text(encoding="utf-8"))
        if contenido.get("version") == VERSION_CACHE:
            return _desde_json(contenido)
    except (OSError, ValueError, KeyError, TypeError):
        pass
    validacion = calcular()
    try:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(json.dumps(_a_json(validacion), ensure_ascii=False, indent=1), encoding="utf-8")
    except OSError:
        pass
    return validacion
