"""Estado de la portada: carrera en vivo entre FIFO y la propuesta del grupo."""

from __future__ import annotations

import asyncio

import reflex as rx

from laboratorio_paginas.core import presets
from laboratorio_paginas.core.secuencias import PROFESOR
from laboratorio_paginas.estado import calculos, vistas

MARCOS_DEMO = 3
SEGUNDOS_POR_PASO_DEMO = 1.25
PAUSA_AL_FINAL = 3.0
VUELTAS_DEMO = 3
"""La demo da unas vueltas y se detiene; así no queda corriendo para siempre."""


def _pasos_propuesta() -> tuple[vistas.PasoVista, ...]:
    return calculos.vistas_bits(PROFESOR.texto, MARCOS_DEMO, presets.PROPUESTA.config)


def _pasos_fifo() -> tuple[vistas.PasoVista, ...]:
    return calculos.vistas_base("fifo", PROFESOR.texto, MARCOS_DEMO)


class InicioEstado(rx.State):
    """Paso de la demo y si está corriendo."""

    demo_paso: int = 0
    demo_corriendo: bool = False
    _demo_ejecucion: int = 0

    @rx.var(deps=["demo_paso"], auto_deps=False)
    def demo_propuesta(self) -> vistas.PasoVista:
        """Instantánea de la propuesta."""
        return _pasos_propuesta()[self.demo_paso]

    @rx.var(deps=["demo_paso"], auto_deps=False)
    def demo_fifo(self) -> vistas.PasoVista:
        """Instantánea de FIFO."""
        return _pasos_fifo()[self.demo_paso]

    @rx.var(deps=["demo_paso"], auto_deps=False)
    def digitos_propuesta(self) -> list[str]:
        """Marcador de la propuesta."""
        return vistas.digitos(_pasos_propuesta()[self.demo_paso].fallos)

    @rx.var(deps=["demo_paso"], auto_deps=False)
    def digitos_fifo(self) -> list[str]:
        """Marcador de FIFO."""
        return vistas.digitos(_pasos_fifo()[self.demo_paso].fallos)

    @rx.var
    def referencias_demo(self) -> list[vistas.ReferenciaVista]:
        """La secuencia del profesor para el bus de la portada."""
        propio = calculos.simular_bits(PROFESOR.texto, MARCOS_DEMO, presets.PROPUESTA.config)
        fifo = calculos.simular_base("fifo", PROFESOR.texto, MARCOS_DEMO)
        return vistas.referencias(propio, fifo)

    @rx.event
    def al_cargar(self):
        """Arranca la demo al abrir la portada."""
        if not self.demo_corriendo:
            return InicioEstado.correr_demo
        return None

    @rx.event
    def alternar_demo(self):
        """Pausa o reanuda la demo."""
        if self.demo_corriendo:
            self.demo_corriendo = False
            return None
        return InicioEstado.correr_demo

    @rx.event(background=True)
    async def correr_demo(self) -> None:
        """Avanza la carrera paso a paso; al final espera y vuelve a empezar."""
        async with self:
            self._demo_ejecucion += 1
            mia = self._demo_ejecucion
            self.demo_corriendo = True
        total = len(_pasos_fifo()) - 1
        for _ in range(VUELTAS_DEMO * (total + 1)):
            async with self:
                if not self.demo_corriendo or self._demo_ejecucion != mia:
                    return
                self.demo_paso = 0 if self.demo_paso >= total else self.demo_paso + 1
                final = self.demo_paso == total
            await asyncio.sleep(PAUSA_AL_FINAL if final else SEGUNDOS_POR_PASO_DEMO)
        async with self:
            if self._demo_ejecucion == mia:
                self.demo_corriendo = False
                self.demo_paso = total
