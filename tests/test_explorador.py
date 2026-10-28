"""Explorador: valores 10.3, deduplicación correcta y desempates."""

from __future__ import annotations

from collections import defaultdict

from laboratorio_paginas.core.algoritmos.fifo_bits import contar_fallos
from laboratorio_paginas.core.explorador import (
    ORDENES,
    espacio,
    explorar,
    firma,
    mapa_calor,
    representante,
)
from laboratorio_paginas.core.modelos import (
    CONTADORES_PERMITIDOS,
    ENVEJECIMIENTOS_PERMITIDOS,
    HISTORIAS_PERMITIDAS,
    ConfigBits,
    OrdenReglas,
)
from laboratorio_paginas.core.secuencias import generar_con_localidad, precargada


def test_profesor_3_marcos_minimo_9() -> None:
    exploracion = explorar(precargada("profesor"), 3)
    assert exploracion.mejor.fallos == 9
    assert all(p.fallos >= 9 for p in exploracion.puntajes)


def test_belady_3_marcos_nadie_baja_de_9() -> None:
    exploracion = explorar(precargada("belady"), 3)
    assert exploracion.mejor.fallos == 9
    assert exploracion.fallos_fifo == 9


def test_belady_4_marcos_minimo_6() -> None:
    assert explorar(precargada("belady"), 4).mejor.fallos == 6


def _todas() -> list[ConfigBits]:
    return [
        ConfigBits(historia=k, contador=c, envejecimiento=e, orden=o)
        for k in HISTORIAS_PERMITIDAS
        for c in CONTADORES_PERMITIDOS
        for e in ENVEJECIMIENTOS_PERMITIDOS
        for o in ORDENES
    ]


def test_espacio_sin_duplicados() -> None:
    firmas = [firma(c) for c in espacio()]
    assert len(firmas) == len(set(firmas))
    assert len(espacio()) < len(_todas())


def test_ejemplos_de_equivalencia_del_enunciado() -> None:
    sin_historia = [firma(ConfigBits(0, 2, 4, o)) for o in (OrdenReglas.PROPUESTA, OrdenReglas.USO_PRIMERO)]
    assert sin_historia[0] == sin_historia[1]
    assert firma(ConfigBits(3, 0, 4)) == firma(ConfigBits(3, 0, 0))


def test_combinaciones_equivalentes_dan_lo_mismo_siempre() -> None:
    """La deduplicación no puede esconder diferencias reales."""
    grupos: dict[tuple[object, ...], list[ConfigBits]] = defaultdict(list)
    for config in _todas():
        grupos[firma(config)].append(config)
    secuencias = [generar_con_localidad(s) for s in range(1, 31)] + [precargada("profesor"), precargada("belady")]
    for miembros in grupos.values():
        if len(miembros) == 1:
            continue
        for secuencia in secuencias:
            for marcos in (2, 3, 4):
                fallos = {contar_fallos(c, secuencia, marcos) for c in miembros}
                assert len(fallos) == 1, miembros


def test_representante_es_el_mas_barato() -> None:
    assert representante(ConfigBits(4, 3, 8, OrdenReglas.SOLO_VENTANA)) == ConfigBits(4, 0, 0, OrdenReglas.SOLO_VENTANA)
    assert representante(ConfigBits(0, 2, 4, OrdenReglas.RECENCIA_PRIMERO)).orden is OrdenReglas.PROPUESTA


def test_ranking_desempata_por_bits_y_propuesta() -> None:
    ranking = explorar(precargada("profesor"), 3).ranking()
    assert len(ranking) == 10
    claves = [(p.fallos, p.costo, p.config.orden is not OrdenReglas.PROPUESTA) for p in ranking]
    assert claves == sorted(claves)
    assert ranking[0].config == ConfigBits(0, 1, 4, OrdenReglas.PROPUESTA)
    assert ranking[0].diferencia_fifo == -3


def test_mapa_calor_cubre_toda_la_rejilla() -> None:
    exploracion = explorar(precargada("profesor"), 3)
    mapa = mapa_calor(exploracion, 8, OrdenReglas.PROPUESTA)
    assert len(mapa) == len(HISTORIAS_PERMITIDAS)
    assert all(len(fila) == len(CONTADORES_PERMITIDOS) for fila in mapa)
    assert mapa[0][0] == exploracion.fallos_fifo
    assert mapa[HISTORIAS_PERMITIDAS.index(4)][2] == 9


def test_curva_y_belady() -> None:
    from laboratorio_paginas.core.algoritmos import Fifo
    from laboratorio_paginas.core.metricas import curva, puntos_belady

    valores = curva(Fifo(), precargada("belady"))
    assert valores[2:4] == (9, 10)
    assert 4 in puntos_belady(valores)


def test_resumen_cuenta_evitados() -> None:
    from laboratorio_paginas.core.algoritmos import Fifo, FifoBits, Optimo
    from laboratorio_paginas.core.metricas import Diferencia, diferencias, resumir

    secuencia = precargada("profesor")
    propio = FifoBits(ConfigBits(4, 2, 8)).simular(secuencia, 3)
    fifo = Fifo().simular(secuencia, 3)
    resumen = resumir(propio, fifo, Optimo().simular(secuencia, 3))
    assert resumen.diferencia_comparacion == -3
    assert resumen.diferencia_optimo == 1
    cambios = diferencias(propio, fifo)
    evitados = [i + 1 for i, d in enumerate(cambios) if d is Diferencia.EVITADO]
    assert evitados == [7, 11, 15]
