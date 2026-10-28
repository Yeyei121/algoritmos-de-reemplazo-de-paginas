"""Parseo, validación de errores y generador con semilla."""

from __future__ import annotations

import pytest

from laboratorio_paginas.core.modelos import Referencia
from laboratorio_paginas.core.secuencias import (
    LONGITUD_GENERADA,
    ErrorSecuencia,
    a_texto,
    generar_con_localidad,
    parsear,
    precargada,
    validar_marcos,
)


def test_parsea_espacios_y_comas() -> None:
    assert parsear("7, 0 1,2") == (Referencia(7), Referencia(0), Referencia(1), Referencia(2))


def test_sufijo_w_marca_escritura() -> None:
    secuencia = parsear("3w 4 5W")
    assert secuencia == (Referencia(3, True), Referencia(4), Referencia(5, True))
    assert a_texto(secuencia) == "3w 4 5w"


def test_mensaje_para_token_invalido() -> None:
    with pytest.raises(ErrorSecuencia) as error:
        parsear("1 a 2")
    esperado = "«a» no es una página válida. Usa números de 0 a 99 separados por espacios o comas"
    assert str(error.value).startswith(esperado)


@pytest.mark.parametrize("texto", ["", "   ", ",,"])
def test_secuencia_vacia(texto: str) -> None:
    with pytest.raises(ErrorSecuencia, match="vacía"):
        parsear(texto)


def test_pagina_fuera_de_rango() -> None:
    with pytest.raises(ErrorSecuencia, match="fuera de rango"):
        parsear("1 100")


def test_limite_de_longitud() -> None:
    assert len(parsear(" ".join(["1"] * 60))) == 60
    with pytest.raises(ErrorSecuencia, match="máximo 60"):
        parsear(" ".join(["1"] * 61))


@pytest.mark.parametrize("marcos", [0, 9])
def test_marcos_fuera_de_rango(marcos: int) -> None:
    with pytest.raises(ErrorSecuencia):
        validar_marcos(marcos)


def test_precargadas() -> None:
    assert a_texto(precargada("profesor")) == "7 0 1 2 0 3 0 4 2 3 0 3 2 1 2 0"
    assert len(precargada("silberschatz")) == 20
    assert len(precargada("belady")) == 12


def test_generador_determinista() -> None:
    assert generar_con_localidad(1) == generar_con_localidad(1)
    assert generar_con_localidad(1) != generar_con_localidad(2)
    secuencia = generar_con_localidad(42)
    assert len(secuencia) == LONGITUD_GENERADA
    assert all(0 <= ref.pagina < 8 for ref in secuencia)
