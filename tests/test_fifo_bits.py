"""FIFO con bits: tabla 10.1 (Propuesta), traza 10.2, explicaciones y bits extra."""

from __future__ import annotations

import random

import pytest

from laboratorio_paginas.core.algoritmos.fifo_bits import FifoBits, contar_fallos
from laboratorio_paginas.core.explorador import espacio
from laboratorio_paginas.core.modelos import ConfigBits, OrdenReglas, Regla
from laboratorio_paginas.core.secuencias import generar_con_localidad, parsear, precargada

PROPUESTA = ConfigBits(historia=4, contador=2, envejecimiento=8, orden=OrdenReglas.PROPUESTA)

TABLA_10_1_PROPUESTA = {
    ("profesor", 2): 14,
    ("profesor", 3): 9,
    ("profesor", 4): 7,
    ("profesor", 5): 6,
    ("silberschatz", 2): 18,
    ("silberschatz", 3): 10,
    ("silberschatz", 4): 8,
    ("belady", 2): 12,
    ("belady", 3): 10,
    ("belady", 4): 8,
}

# Traza 10.2: por paso, celdas «página (H,C)» de los marcos 1 a 3, víctima y envejecimiento.
TRAZA_10_2 = [
    ("7 (1000,0)", "–", "–", None, False),
    ("7 (0100,0)", "0 (1000,0)", "–", None, False),
    ("7 (0010,0)", "0 (0100,0)", "1 (1000,0)", None, False),
    ("2 (1000,0)", "0 (0010,0)", "1 (0100,0)", 7, False),
    ("2 (0100,0)", "0 (1001,1)", "1 (0010,0)", None, False),
    ("2 (0010,0)", "0 (0100,1)", "3 (1000,0)", 1, False),
    ("2 (0001,0)", "0 (1010,2)", "3 (0100,0)", None, False),
    ("4 (1000,0)", "0 (0101,1)", "3 (0010,0)", 2, True),
    ("4 (0100,0)", "0 (0010,1)", "2 (1000,0)", 3, False),
    ("3 (1000,0)", "0 (0001,1)", "2 (0100,0)", 4, False),
    ("3 (0100,0)", "0 (1000,2)", "2 (0010,0)", None, False),
    ("3 (1010,1)", "0 (0100,2)", "2 (0001,0)", None, False),
    ("3 (0101,1)", "0 (0010,2)", "2 (1000,1)", None, False),
    ("1 (1000,0)", "0 (0001,2)", "2 (0100,1)", 3, False),
    ("1 (0100,0)", "0 (0000,2)", "2 (1010,2)", None, False),
    ("1 (0010,0)", "0 (1000,1)", "2 (0101,1)", None, True),
]
FALLOS_TRAZA = {1, 2, 3, 4, 6, 8, 9, 10, 14}


@pytest.mark.parametrize(("clave", "esperado"), TABLA_10_1_PROPUESTA.items(), ids=str)
def test_propuesta_tabla_10_1(clave: tuple[str, int], esperado: int) -> None:
    secuencia, marcos = clave
    assert FifoBits(PROPUESTA).simular(precargada(secuencia), marcos).fallos == esperado
    assert contar_fallos(PROPUESTA, precargada(secuencia), marcos) == esperado


def test_traza_10_2() -> None:
    resultado = FifoBits(PROPUESTA).simular(precargada("profesor"), 3)
    assert resultado.fallos == 9
    for paso, (m1, m2, m3, victima, envejecio) in zip(resultado.pasos, TRAZA_10_2, strict=True):
        celdas = tuple("–" if m.pagina is None else f"{m.pagina} ({m.historia},{m.contador})" for m in paso.marcos)
        assert celdas == (m1, m2, m3), f"paso {paso.indice}"
        assert paso.victima == victima, f"paso {paso.indice}"
        assert paso.envejecimiento == envejecio, f"paso {paso.indice}"
        assert paso.fallo == (paso.indice in FALLOS_TRAZA), f"paso {paso.indice}"


def test_frase_del_paso_14() -> None:
    paso = FifoBits(PROPUESTA).simular(precargada("profesor"), 3).pasos[13]
    assert paso.decision is not None
    assert paso.decision.frase == (
        "Sale la 3: después de la regla de uso empataban la 2 y la 3 (C = 1), "
        "y la 3 tenía la historia más baja (0101 < 1000)."
    )
    assert paso.decision.regla_decisiva is Regla.RECENCIA
    reglas = [p.regla for p in paso.decision.pasos]
    assert reglas == [Regla.VENTANA, Regla.USO, Regla.RECENCIA]
    assert paso.decision.pasos[1].antes == (3, 0, 2)
    assert paso.decision.pasos[1].despues == (3, 2)


def test_todos_los_reemplazos_tienen_explicacion() -> None:
    for config in espacio():
        for paso in FifoBits(config).simular(precargada("silberschatz"), 3).pasos:
            if paso.victima is not None:
                assert paso.decision is not None
                assert paso.decision.frase.startswith(f"Sale la {paso.victima}:")
                assert paso.decision.pasos[-1].despues == (paso.victima,)


def test_version_rapida_coincide_con_la_completa() -> None:
    azar = random.Random(7)
    configs = espacio()
    for semilla in range(40):
        secuencia = generar_con_localidad(semilla)
        config = azar.choice(configs)
        marcos = azar.randint(1, 6)
        assert contar_fallos(config, secuencia, marcos) == FifoBits(config).simular(secuencia, marcos).fallos


def test_costo_en_bits() -> None:
    assert PROPUESTA.costo_bits == 6
    assert ConfigBits(historia=3, contador=2, envejecimiento=8).costo_bits == 5
    assert ConfigBits(historia=8, contador=3, modificada=True, fijada=True).costo_bits == 13


def test_contador_satura() -> None:
    config = ConfigBits(historia=0, contador=1)
    resultado = FifoBits(config).simular(parsear("5 5 5 5"), 2)
    assert [p.marcos[0].contador for p in resultado.pasos] == [0, 1, 1, 1]


def test_pagina_fijada_no_sale() -> None:
    config = ConfigBits(fijada=True, paginas_fijadas=frozenset({1}))
    resultado = FifoBits(config).simular(parsear("1 2 3 4 5"), 2)
    victimas = [p.victima for p in resultado.pasos if p.victima is not None]
    assert 1 not in victimas
    assert "fijada" in resultado.pasos[2].decision.frase  # type: ignore[union-attr]


def test_si_todas_estan_fijadas_sale_la_mas_antigua() -> None:
    config = ConfigBits(fijada=True, paginas_fijadas=frozenset({1, 2}))
    resultado = FifoBits(config).simular(parsear("1 2 3"), 2)
    assert resultado.pasos[-1].victima == 1


def test_bit_m_prefiere_paginas_limpias_y_ahorra_escrituras() -> None:
    secuencia = parsear("1w 2 3 1 4")
    sin_m = FifoBits(ConfigBits()).simular(secuencia, 2)
    con_m = FifoBits(ConfigBits(modificada=True)).simular(secuencia, 2)
    assert sin_m.pasos[2].victima == 1
    assert con_m.pasos[2].victima == 2
    assert con_m.escrituras_disco < sin_m.escrituras_disco
    assert con_m.pasos[2].decision.regla_decisiva is Regla.MODIFICADA  # type: ignore[union-attr]


def test_escritura_en_acierto_marca_m() -> None:
    resultado = FifoBits(ConfigBits(modificada=True)).simular(parsear("1 1w"), 1)
    assert resultado.pasos[1].marcos[0].modificada


def test_envejecimiento_solo_si_hay_contador() -> None:
    config = ConfigBits(historia=2, contador=0, envejecimiento=4)
    resultado = FifoBits(config).simular(precargada("profesor"), 3)
    assert not any(p.envejecimiento for p in resultado.pasos)


@pytest.mark.parametrize("valor", [1, 5, 9])
def test_config_invalida(valor: int) -> None:
    with pytest.raises(ValueError):
        ConfigBits(historia=valor)
