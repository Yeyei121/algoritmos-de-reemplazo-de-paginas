"""Constantes de tema. Los colores y tamaños viven en assets/tokens.css."""

from __future__ import annotations

HOJAS_DE_ESTILO: tuple[str, ...] = ("/fuentes.css", "/tokens.css", "/componentes.css", "/animaciones.css")
"""Las fuentes IBM Plex van dentro de assets/fuentes para que la app funcione sin internet."""
SCRIPTS: tuple[str, ...] = ("/atajos.js",)

# Colores para la gráfica (recharts necesita valores, no variables CSS).
COLOR_FIFO = "#a9bfb2"
COLOR_CONFIG = "#ffb627"
COLOR_OPTIMO = "#5bc8e8"
COLOR_LRU = "#e8a867"
COLOR_SEGUNDA = "#f0eee3"
COLOR_BELADY = "#f25c54"
COLOR_REJILLA = "#2c6b52"
