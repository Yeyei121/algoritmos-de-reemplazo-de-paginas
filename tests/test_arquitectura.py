"""El motor es Python puro: core/ no puede depender de Reflex."""

from __future__ import annotations

import ast
from pathlib import Path

CORE = Path(__file__).resolve().parent.parent / "laboratorio_paginas" / "core"


def test_core_no_importa_reflex() -> None:
    for archivo in CORE.rglob("*.py"):
        arbol = ast.parse(archivo.read_text(encoding="utf-8"))
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.Import):
                nombres = [a.name for a in nodo.names]
            elif isinstance(nodo, ast.ImportFrom):
                nombres = [nodo.module or ""]
            else:
                continue
            assert not any(n.split(".")[0] == "reflex" for n in nombres), archivo.name
