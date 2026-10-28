"""Validación con el generador exacto (sección 10.4)."""

from __future__ import annotations

import pytest

from laboratorio_paginas.core import validacion
from laboratorio_paginas.core.modelos import ConfigBits, OrdenReglas

RECOMENDADA = ConfigBits(historia=3, contador=2, envejecimiento=8, orden=OrdenReglas.PROPUESTA)
TOLERANCIA = 0.1

PROMEDIOS = {
    3: {"Recomendada": 15.99, "FIFO": 16.85, "LRU": 16.07, "2.ª oportunidad": 16.67, "Óptimo": 12.10},
    4: {"Recomendada": 12.36, "FIFO": 13.20, "LRU": 12.35, "2.ª oportunidad": 12.88, "Óptimo": 9.52},
}
ENTRENAMIENTO = {3: 7843, 4: 6133}


@pytest.fixture(scope="module")
def resultado() -> validacion.Validacion:
    return validacion.calcular()


def test_recomendada_y_entrenamiento(resultado: validacion.Validacion) -> None:
    for fila in resultado.por_marcos:
        assert fila.recomendada == RECOMENDADA
        assert fila.recomendada.costo_bits == 5
        assert fila.entrenamiento_recomendada == ENTRENAMIENTO[fila.marcos]


def test_promedios_de_prueba(resultado: validacion.Validacion) -> None:
    for fila in resultado.por_marcos:
        for nombre, esperado in PROMEDIOS[fila.marcos].items():
            assert fila.promedios_prueba[nombre] == pytest.approx(esperado, abs=TOLERANCIA), nombre


def test_contraejemplo_un_bit(resultado: validacion.Validacion) -> None:
    assert resultado.contraejemplo_profesor == 9
    assert resultado.contraejemplo_prueba == pytest.approx(16.45, abs=TOLERANCIA)
    assert resultado.contraejemplo_prueba > PROMEDIOS[3]["Recomendada"]


def test_casos_donde_no_gana_quedan_a_la_vista(resultado: validacion.Validacion) -> None:
    filas = {(f.secuencia, f.marcos): f.fallos for f in resultado.clasicas}
    assert filas[("Profesor (16)", 2)]["Recomendada"] > filas[("Profesor (16)", 2)]["FIFO"]
    assert filas[("Belady (12)", 3)]["Recomendada"] > filas[("Belady (12)", 3)]["FIFO"]


def test_cache_en_disco(tmp_path: object, resultado: validacion.Validacion) -> None:
    ruta = tmp_path / "validacion.json"  # type: ignore[operator]
    datos = validacion._a_json(resultado)
    import json

    ruta.write_text(json.dumps(datos), encoding="utf-8")
    leida = validacion.obtener.__wrapped__(ruta)
    assert leida == resultado
