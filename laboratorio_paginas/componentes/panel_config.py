"""Panel de la izquierda: secuencia, marcos y configuración de bits."""

from __future__ import annotations

import reflex as rx

from laboratorio_paginas.componentes.comunes import boton_icono, campo, segmentos
from laboratorio_paginas.core import presets
from laboratorio_paginas.core.modelos import (
    CONTADORES_PERMITIDOS,
    HISTORIAS_PERMITIDAS,
    NOMBRES_ORDEN,
    OrdenReglas,
)
from laboratorio_paginas.core.secuencias import MARCOS_MAXIMOS, MARCOS_MINIMOS, PRECARGADAS
from laboratorio_paginas.estado.app import COMPARACIONES, FUENTE_ALEATORIA, FUENTE_PROPIA, EstadoApp

FUENTES: tuple[tuple[str, str], ...] = (
    *[(item.clave, item.nombre) for item in PRECARGADAS],
    (FUENTE_PROPIA, "Secuencia propia"),
    (FUENTE_ALEATORIA, "Aleatoria con localidad"),
)
ENVEJECIMIENTOS: tuple[tuple[str, str], ...] = (("0", "Apagado"), ("4", "Cada 4"), ("8", "Cada 8"))


def entrada_secuencia(despues: rx.EventHandler | None = None) -> rx.Component:
    """Selector de secuencia, texto editable, generador y número de marcos."""
    al_enviar = [EstadoApp.enviar_secuencia]
    if despues is not None:
        al_enviar.append(despues)
    return rx.el.div(
        campo(
            "Secuencia",
            rx.el.select(
                *[rx.el.option(texto, value=clave) for clave, texto in FUENTES],
                value=EstadoApp.fuente,
                on_change=EstadoApp.elegir_fuente,
                class_name="selector",
                aria_label="Secuencia precargada",
            ),
        ),
        rx.el.form(
            rx.el.textarea(
                default_value=EstadoApp.texto,
                key=EstadoApp.texto,
                name="secuencia",
                rows=3,
                class_name="entrada mono",
                aria_label="Referencias separadas por espacios o comas",
                aria_invalid=EstadoApp.error != "",
                aria_describedby="ayuda-secuencia",
                spell_check=False,
            ),
            rx.el.small(
                "Páginas de 0 a 99 separadas por espacios o comas, hasta 60. Agrega w para escritura: 3w.",
                id="ayuda-secuencia",
                class_name="tenue",
                style={"font-size": "var(--t-14)"},
            ),
            rx.cond(EstadoApp.error != "", rx.el.p(EstadoApp.error, class_name="mensaje-error", role="alert")),
            rx.el.div(
                rx.el.button("Usar esta secuencia", type="submit", class_name="boton"),
                rx.cond(
                    EstadoApp.fuente == FUENTE_ALEATORIA,
                    boton_icono("shuffle", "Generar otra", EstadoApp.generar_otra, ocultar_texto_en_movil=False),
                ),
                class_name="config-fila",
            ),
            on_submit=al_enviar,
            reset_on_submit=False,
            class_name="campo",
        ),
        campo(
            "Marcos",
            segmentos(
                "marcos",
                [(str(n), str(n)) for n in range(MARCOS_MINIMOS, MARCOS_MAXIMOS + 1)],
                EstadoApp.marcos.to_string(),
                EstadoApp.set_marcos,
                "Número de marcos",
            ),
        ),
        class_name="config-grupo",
    )


def _presets() -> rx.Component:
    opciones = [(p.clave, p.nombre, p.descripcion) for p in presets.todos()]
    opciones.append(("personalizada", "Personalizada", "Lo que armes con los selectores de abajo."))
    return rx.el.fieldset(
        rx.el.legend("Configuraciones con nombre", class_name="campo-titulo"),
        rx.el.div(
            *[
                rx.el.label(
                    rx.el.input(
                        type="radio",
                        name="preset",
                        value=clave,
                        checked=EstadoApp.preset == clave,
                        on_change=EstadoApp.aplicar_preset,
                        disabled=clave == "personalizada",
                    ),
                    rx.el.strong(nombre),
                    rx.el.small(descripcion),
                    class_name="preset",
                )
                for clave, nombre, descripcion in opciones
            ],
            class_name="presets",
        ),
        style={"border": "0", "padding": "0", "margin": "0"},
    )


def _bits() -> rx.Component:
    return rx.el.div(
        campo(
            "Historia H (bits de la ventana)",
            segmentos(
                "historia",
                [(str(k), str(k)) for k in HISTORIAS_PERMITIDAS],
                EstadoApp.historia.to_string(),
                EstadoApp.set_historia,
                "Bits de historia",
            ),
        ),
        campo(
            "Contador de uso C (bits)",
            segmentos(
                "contador",
                [(str(c), str(c)) for c in CONTADORES_PERMITIDOS],
                EstadoApp.contador.to_string(),
                EstadoApp.set_contador,
                "Bits del contador",
            ),
        ),
        campo(
            "Envejecimiento de C",
            segmentos(
                "envejecimiento",
                list(ENVEJECIMIENTOS),
                EstadoApp.envejecimiento.to_string(),
                EstadoApp.set_envejecimiento,
                "Envejecimiento",
            ),
        ),
        campo(
            "Orden de las reglas de salida",
            rx.el.select(
                *[rx.el.option(NOMBRES_ORDEN[o], value=o.value) for o in OrdenReglas],
                value=EstadoApp.orden,
                on_change=EstadoApp.set_orden,
                class_name="selector",
                aria_label="Orden de las reglas",
            ),
            rx.el.div(
                rx.foreach(EstadoApp.cadena_reglas, lambda r: rx.el.span(r)),
                class_name="cadena",
                aria_label="Reglas que se aplican, en orden",
            ),
        ),
        class_name="config-grupo",
    )


def _extras() -> rx.Component:
    return rx.el.div(
        rx.el.label(
            rx.el.input(type="checkbox", checked=EstadoApp.usa_m, on_change=EstadoApp.alternar_m(~EstadoApp.usa_m)),
            rx.el.span("Bit M (modificada): prefiere sacar páginas que no hay que escribir en disco"),
            class_name="interruptor",
        ),
        rx.el.label(
            rx.el.input(type="checkbox", checked=EstadoApp.usa_p, on_change=EstadoApp.alternar_p(~EstadoApp.usa_p)),
            rx.el.span("Bit P (fijada): las páginas fijadas no salen"),
            class_name="interruptor",
        ),
        rx.cond(
            EstadoApp.usa_p,
            campo(
                "Páginas fijadas",
                rx.el.div(
                    rx.foreach(
                        EstadoApp.paginas_secuencia,
                        lambda p: rx.el.button(
                            p,
                            type="button",
                            class_name="boton",
                            aria_pressed=EstadoApp.fijadas.contains(p),
                            on_click=EstadoApp.alternar_fijada(p),
                        ),
                    ),
                    class_name="fijadas",
                ),
            ),
        ),
        class_name="config-grupo",
    )


def panel_configuracion() -> rx.Component:
    """Todo lo que el usuario puede ajustar en el laboratorio."""
    return rx.el.aside(
        rx.el.h2("Configuración"),
        rx.el.div(
            entrada_secuencia(),
            rx.el.div(_presets(), class_name="config-grupo"),
            _bits(),
            _extras(),
            rx.el.div(
                rx.el.div(
                    rx.el.strong(EstadoApp.costo_bits),
                    rx.el.span(rx.cond(EstadoApp.costo_bits == 1, "bit por marco", "bits por marco")),
                    class_name="costo",
                ),
                rx.el.span("Costo: k + bits de C + M + P.", class_name="tenue", style={"font-size": "var(--t-14)"}),
                class_name="config-grupo",
            ),
            rx.el.div(
                campo(
                    "Comparar contra",
                    segmentos(
                        "comparar",
                        list(COMPARACIONES.items()),
                        EstadoApp.comparar,
                        EstadoApp.set_comparar,
                        "Algoritmo de comparación",
                    ),
                ),
                class_name="config-grupo",
            ),
            class_name="config",
        ),
        class_name="zona lab-config",
    )
