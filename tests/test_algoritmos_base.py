"""Algoritmos base contra la tabla 10.1 y contra las hojas del Excel del profesor."""

from __future__ import annotations

import pytest

from laboratorio_paginas.core.algoritmos.fifo import Fifo
from laboratorio_paginas.core.algoritmos.fifo_bits import FifoBits
from laboratorio_paginas.core.algoritmos.lru import Lru
from laboratorio_paginas.core.algoritmos.mru import Mru
from laboratorio_paginas.core.algoritmos.optimo import Optimo
from laboratorio_paginas.core.algoritmos.segunda_oportunidad import SegundaOportunidad
from laboratorio_paginas.core.modelos import ConfigBits, Resultado
from laboratorio_paginas.core.secuencias import PRECARGADAS, parsear, precargada
from tests.datos_profesor import SEGUNDA_OPORTUNIDAD, SEGUNDA_OPORTUNIDAD_SALE, TABLAS

ALGORITMOS = {"Óptimo": Optimo(), "FIFO": Fifo(), "LRU": Lru(), "MRU": Mru(), "2.ª oportunidad": SegundaOportunidad()}

# (secuencia, marcos): Óptimo, FIFO, LRU, MRU, 2.ª oportunidad
TABLA_10_1 = {
    ("profesor", 2): (11, 13, 13, 16, 13),
    ("profesor", 3): (8, 12, 11, 14, 12),
    ("profesor", 4): (7, 9, 7, 12, 8),
    ("profesor", 5): (6, 6, 6, 9, 6),
    ("silberschatz", 2): (13, 15, 17, 18, 15),
    ("silberschatz", 3): (9, 15, 12, 16, 14),
    ("silberschatz", 4): (8, 10, 8, 12, 9),
    ("belady", 2): (9, 12, 12, 10, 12),
    ("belady", 3): (7, 9, 10, 7, 9),
    ("belady", 4): (6, 10, 8, 6, 10),
}


@pytest.mark.parametrize(("clave", "esperado"), TABLA_10_1.items(), ids=lambda v: str(v))
def test_fallos_tabla_10_1(clave: tuple[str, int], esperado: tuple[int, ...]) -> None:
    secuencia, marcos = clave
    obtenido = tuple(alg.simular(precargada(secuencia), marcos).fallos for alg in ALGORITMOS.values())
    assert obtenido == esperado


def _filas(resultado: Resultado) -> list[str]:
    filas = []
    for marco in range(resultado.numero_marcos):
        celdas = [paso.marcos[marco].pagina for paso in resultado.pasos]
        filas.append(" ".join("-" if c is None else str(c) for c in celdas))
    return filas


def _salidas(resultado: Resultado) -> str:
    return " ".join("-" if p.victima is None else str(p.victima) for p in resultado.pasos)


@pytest.mark.parametrize(("clave", "tabla"), TABLAS.items(), ids=lambda v: str(v)[:30])
def test_tablas_del_excel(clave: tuple[str, str, int], tabla: tuple[list[str], str | None]) -> None:
    nombre, texto, marcos = clave
    filas, sale = tabla
    resultado = ALGORITMOS[nombre].simular(parsear(texto), marcos)
    assert _filas(resultado) == filas
    if sale is not None:
        assert _salidas(resultado) == sale


def test_segunda_oportunidad_igual_a_la_hoja_del_profesor() -> None:
    resultado = SegundaOportunidad().simular(precargada("profesor"), 3)
    for paso in resultado.pasos:
        for marco in paso.marcos:
            pagina, bit, puntero = SEGUNDA_OPORTUNIDAD[marco.indice][paso.indice - 1]
            assert marco.pagina == pagina, f"paso {paso.indice}, marco {marco.indice + 1}"
            assert marco.bit_r == bit, f"paso {paso.indice}, marco {marco.indice + 1}"
            assert marco.puntero == (puntero == "*"), f"paso {paso.indice}, marco {marco.indice + 1}"
    assert _salidas(resultado) == SEGUNDA_OPORTUNIDAD_SALE
    assert resultado.fallos == 12


@pytest.mark.parametrize("item", PRECARGADAS, ids=lambda i: i.clave)
@pytest.mark.parametrize("marcos", range(1, 7))
def test_fifo_puro_igual_a_fifo(item: object, marcos: int) -> None:
    secuencia = parsear(item.texto)  # type: ignore[attr-defined]
    fifo = Fifo().simular(secuencia, marcos)
    puro = FifoBits(ConfigBits(historia=0, contador=0)).simular(secuencia, marcos)
    assert puro.fallos == fifo.fallos
    assert _filas(puro) == _filas(fifo)
    assert _salidas(puro) == _salidas(fifo)


def test_fallos_incluyen_cargas_iniciales() -> None:
    resultado = Fifo().simular(parsear("1 2 3"), 3)
    assert resultado.fallos == 3
    assert resultado.aciertos == 0
    assert resultado.tasa_fallos == pytest.approx(100.0)


def test_optimo_desempata_por_marco_menor() -> None:
    resultado = Optimo().simular(parsear("1 2 3 4"), 3)
    assert resultado.pasos[-1].victima == 1
    assert "marco más bajo" in resultado.pasos[-1].decision.frase  # type: ignore[union-attr]


def test_cada_reemplazo_trae_frase() -> None:
    for alg in ALGORITMOS.values():
        for paso in alg.simular(precargada("silberschatz"), 3).pasos:
            if paso.victima is not None:
                assert paso.decision is not None
                assert paso.decision.frase.startswith(f"Sale la {paso.victima}:")


def test_escrituras_a_disco_se_cuentan_en_todos() -> None:
    secuencia = parsear("1w 2 3 4")
    for alg in ALGORITMOS.values():
        resultado = alg.simular(secuencia, 3)
        assert resultado.escrituras_disco == int(resultado.pasos[-1].victima == 1)
