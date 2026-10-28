"""Secuencias de referencias: parseo, validación, precargadas y generador."""

from __future__ import annotations

import random
import re
from dataclasses import dataclass

from laboratorio_paginas.core.modelos import Referencia

PAGINA_MINIMA = 0
PAGINA_MAXIMA = 99
LONGITUD_MINIMA = 1
LONGITUD_MAXIMA = 60
MARCOS_MINIMOS = 1
MARCOS_MAXIMOS = 8
SUFIJO_ESCRITURA = "w"

# Parámetros del generador con localidad (sección 6.6 del enunciado).
PAGINAS_GENERADOR = 8
TAMANO_BASE = 3
LONGITUD_GENERADA = 40
PROB_CAMBIO_BASE = 0.1
PROB_LOCALIDAD = 0.8

_SEPARADORES = re.compile(r"[\s,;]+")
_TOKEN = re.compile(r"^(\d+)([wW]?)$")

Secuencia = tuple[Referencia, ...]


@dataclass(frozen=True)
class SecuenciaPrecargada:
    """Secuencia con nombre que aparece en el selector."""

    clave: str
    nombre: str
    texto: str
    descripcion: str


PROFESOR = SecuenciaPrecargada(
    clave="profesor",
    nombre="Profesor (16)",
    texto="7 0 1 2 0 3 0 4 2 3 0 3 2 1 2 0",
    descripcion="La del Excel del profesor.",
)
SILBERSCHATZ = SecuenciaPrecargada(
    clave="silberschatz",
    nombre="Silberschatz (20)",
    texto="7 0 1 2 0 3 0 4 2 3 0 3 2 1 2 0 1 7 0 1",
    descripcion="La secuencia completa del libro de Silberschatz.",
)
BELADY = SecuenciaPrecargada(
    clave="belady",
    nombre="Belady (12)",
    texto="1 2 3 4 1 2 5 1 2 3 4 5",
    descripcion="Con FIFO da más fallos con 4 marcos que con 3.",
)
PRECARGADAS: tuple[SecuenciaPrecargada, ...] = (PROFESOR, SILBERSCHATZ, BELADY)


class ErrorSecuencia(ValueError):
    """Error de entrada con un mensaje listo para mostrar al usuario."""


def parsear(texto: str) -> Secuencia:
    """Convierte «7 0 1 3w» en referencias, o lanza ErrorSecuencia."""
    tokens = [t for t in _SEPARADORES.split(texto.strip()) if t]
    if not tokens:
        raise ErrorSecuencia("La secuencia está vacía. Escribe páginas de 0 a 99 separadas por espacios o comas.")
    referencias: list[Referencia] = []
    for token in tokens:
        coincidencia = _TOKEN.match(token)
        if coincidencia is None:
            raise ErrorSecuencia(
                f"«{token}» no es una página válida. "
                "Usa números de 0 a 99 separados por espacios o comas; agrega w para escritura (3w)."
            )
        pagina = int(coincidencia.group(1))
        if not PAGINA_MINIMA <= pagina <= PAGINA_MAXIMA:
            raise ErrorSecuencia(f"La página {pagina} está fuera de rango. Usa páginas de 0 a 99.")
        referencias.append(Referencia(pagina, escritura=bool(coincidencia.group(2))))
    if len(referencias) > LONGITUD_MAXIMA:
        raise ErrorSecuencia(f"La secuencia tiene {len(referencias)} referencias. Deja como máximo {LONGITUD_MAXIMA}.")
    return tuple(referencias)


def validar_marcos(marcos: int) -> int:
    """Devuelve el número de marcos si está en rango, o lanza ErrorSecuencia."""
    if not MARCOS_MINIMOS <= marcos <= MARCOS_MAXIMOS:
        raise ErrorSecuencia(f"Elige entre {MARCOS_MINIMOS} y {MARCOS_MAXIMOS} marcos.")
    return marcos


def a_texto(secuencia: Secuencia) -> str:
    """Convierte referencias de vuelta a texto («7 0 1 3w»)."""
    return " ".join(str(ref) for ref in secuencia)


def desde_paginas(paginas: list[int] | tuple[int, ...]) -> Secuencia:
    """Crea una secuencia de solo lecturas a partir de números."""
    return tuple(Referencia(p) for p in paginas)


def precargada(clave: str) -> Secuencia:
    """Devuelve una secuencia precargada por su clave."""
    for item in PRECARGADAS:
        if item.clave == clave:
            return parsear(item.texto)
    raise KeyError(clave)


def generar_con_localidad(semilla: int) -> Secuencia:
    """Genera 40 referencias con localidad, siempre iguales para la misma semilla.

    Sigue al pie de la letra el orden de llamadas al generador del enunciado,
    para que los números de la validación coincidan.
    """
    rng = random.Random(semilla)
    base = rng.sample(range(PAGINAS_GENERADOR), TAMANO_BASE)
    paginas: list[int] = []
    for _ in range(LONGITUD_GENERADA):
        if rng.random() < PROB_CAMBIO_BASE:
            base = rng.sample(range(PAGINAS_GENERADOR), TAMANO_BASE)
        if rng.random() < PROB_LOCALIDAD:
            paginas.append(rng.choice(base))
        else:
            paginas.append(rng.randrange(PAGINAS_GENERADOR))
    return desde_paginas(paginas)
