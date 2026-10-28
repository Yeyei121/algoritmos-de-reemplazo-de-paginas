"""Configuración de Reflex."""

import reflex as rx

config = rx.Config(
    app_name="laboratorio_paginas",
    telemetry_enabled=False,
    show_built_with_reflex=False,
    disable_plugins=[rx.plugins.SitemapPlugin],
)
