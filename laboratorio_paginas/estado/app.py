"""Estado compartido: secuencia, marcos, configuración de bits y paso del laboratorio.

Las demás pantallas heredan de este estado, así la secuencia y la configuración
son las mismas en toda la app.
"""

from __future__ import annotations

import asyncio

import reflex as rx

from laboratorio_paginas.core import presets
from laboratorio_paginas.core.modelos import NOMBRES_ORDEN, NOMBRES_REGLA, ConfigBits, OrdenReglas
from laboratorio_paginas.core.secuencias import (
    MARCOS_MAXIMOS,
    MARCOS_MINIMOS,
    PRECARGADAS,
    PROFESOR,
    ErrorSecuencia,
    a_texto,
    generar_con_localidad,
    parsear,
)
from laboratorio_paginas.estado import calculos, vistas

FUENTE_PROPIA = "propia"
FUENTE_ALEATORIA = "aleatoria"
SEMILLA_INICIAL = 1001
"""Las semillas 1 a 1000 son de la validación; el botón «Generar otra» arranca después."""

VELOCIDADES: tuple[str, ...] = ("0.5", "1", "2", "4")
SEGUNDOS_POR_PASO = 1.6
"""Tiempo entre pasos a velocidad 1×."""

COMPARACIONES: dict[str, str] = {"fifo": "FIFO", "segunda": "2.ª oportunidad", "lru": "LRU"}
PRESET_PERSONALIZADA = "personalizada"
RUTA_LABORATORIO = "/laboratorio"

DEPS_SECUENCIA = ["texto", "marcos"]
DEPS_CONFIG = [*DEPS_SECUENCIA, "historia", "contador", "envejecimiento", "orden", "usa_m", "usa_p", "fijadas"]


class EstadoApp(rx.State):
    """Secuencia, configuración y reproducción del laboratorio."""

    texto: str = PROFESOR.texto
    error: str = ""
    fuente: str = PROFESOR.clave
    semilla: int = SEMILLA_INICIAL - 1
    marcos: int = 3

    historia: int = 4
    contador: int = 2
    envejecimiento: int = 8
    orden: str = OrdenReglas.PROPUESTA.value
    usa_m: bool = False
    usa_p: bool = False
    fijadas: list[int] = []
    comparar: str = "fifo"

    paso: int = 0
    reproduciendo: bool = False
    velocidad: str = "1"
    _ejecucion: int = 0

    # ------------------------------------------------------------ ayudas

    def _config(self) -> ConfigBits:
        return ConfigBits(
            historia=self.historia,
            contador=self.contador,
            envejecimiento=self.envejecimiento,
            orden=OrdenReglas(self.orden),
            modificada=self.usa_m,
            fijada=self.usa_p,
            paginas_fijadas=frozenset(self.fijadas) if self.usa_p else frozenset(),
        )

    def _poner_config(self, config: ConfigBits) -> None:
        self.historia = config.historia
        self.contador = config.contador
        self.envejecimiento = config.envejecimiento
        self.orden = config.orden.value
        self.usa_m = config.modificada
        self.usa_p = config.fijada

    def _poner_texto(self, texto: str, fuente: str) -> None:
        self.texto = texto
        self.fuente = fuente
        self.error = ""
        self.paso = 0
        self.reproduciendo = False
        paginas = {r.pagina for r in calculos.secuencia(texto)}
        self.fijadas = [p for p in self.fijadas if p in paginas]

    def _total(self) -> int:
        return len(calculos.secuencia(self.texto))

    # ------------------------------------------------------- vars de config

    @rx.var(deps=DEPS_CONFIG[2:], auto_deps=False)
    def costo_bits(self) -> int:
        """Bits por marco de la configuración actual."""
        return self._config().costo_bits

    @rx.var(deps=DEPS_CONFIG[2:], auto_deps=False)
    def preset(self) -> str:
        """Clave del preset que coincide con la configuración, o «personalizada»."""
        actual = self._config()
        for item in presets.todos():
            if item.config == actual:
                return item.clave
        return PRESET_PERSONALIZADA

    @rx.var(deps=DEPS_CONFIG[2:], auto_deps=False)
    def cadena_reglas(self) -> list[str]:
        """Reglas que de verdad se aplican, en orden."""
        return [NOMBRES_REGLA[r].capitalize() if r.value != "fifo" else "FIFO" for r in self._config().reglas]

    @rx.var(deps=DEPS_CONFIG[2:], auto_deps=False)
    def descripcion(self) -> str:
        """«k 4, C 2 bits, envejecimiento cada 8, Propuesta»."""
        return self._config().describir()

    @rx.var(deps=["orden"], auto_deps=False)
    def nombre_orden(self) -> str:
        """Nombre visible del orden de reglas."""
        return NOMBRES_ORDEN[OrdenReglas(self.orden)]

    @rx.var(deps=["texto"], auto_deps=False)
    def paginas_secuencia(self) -> list[int]:
        """Páginas distintas de la secuencia, para elegir las fijadas."""
        return sorted({r.pagina for r in calculos.secuencia(self.texto)})

    @rx.var(deps=["texto"], auto_deps=False)
    def total_pasos(self) -> int:
        """Número de referencias."""
        return self._total()

    @rx.var(deps=["texto"], auto_deps=False)
    def tiene_escrituras(self) -> bool:
        """True si la secuencia trae referencias de escritura (sufijo w)."""
        return any(r.escritura for r in calculos.secuencia(self.texto))

    @rx.var(deps=["comparar"], auto_deps=False)
    def nombre_comparacion(self) -> str:
        """Nombre del algoritmo de comparación."""
        return COMPARACIONES[self.comparar]

    @rx.var(deps=["velocidad"], auto_deps=False)
    def escala(self) -> str:
        """Multiplicador de duración de las animaciones según la velocidad."""
        return str(1 / float(self.velocidad))

    # ----------------------------------------------------- vars de la placa

    @rx.var(deps=["paso", *DEPS_CONFIG], auto_deps=False)
    def actual(self) -> vistas.PasoVista:
        """Instantánea del paso actual de la configuración."""
        pasos = calculos.vistas_bits(self.texto, self.marcos, self._config())
        return pasos[min(self.paso, len(pasos) - 1)]

    @rx.var(deps=["paso", "comparar", *DEPS_SECUENCIA], auto_deps=False)
    def actual_comparacion(self) -> vistas.PasoVista:
        """Instantánea del paso actual del algoritmo de comparación."""
        pasos = calculos.vistas_base(self.comparar, self.texto, self.marcos)
        return pasos[min(self.paso, len(pasos) - 1)]

    @rx.var(deps=["paso", *DEPS_CONFIG], auto_deps=False)
    def digitos_config(self) -> list[str]:
        """Dígitos del marcador de la configuración."""
        pasos = calculos.vistas_bits(self.texto, self.marcos, self._config())
        return vistas.digitos(pasos[min(self.paso, len(pasos) - 1)].fallos)

    @rx.var(deps=["paso", "comparar", *DEPS_SECUENCIA], auto_deps=False)
    def digitos_comparacion(self) -> list[str]:
        """Dígitos del marcador de la comparación."""
        pasos = calculos.vistas_base(self.comparar, self.texto, self.marcos)
        return vistas.digitos(pasos[min(self.paso, len(pasos) - 1)].fallos)

    @rx.var(deps=["comparar", *DEPS_CONFIG], auto_deps=False)
    def referencias(self) -> list[vistas.ReferenciaVista]:
        """Referencias del bus con su resultado."""
        propio = calculos.simular_bits(self.texto, self.marcos, self._config())
        otro = calculos.simular_base(self.comparar, self.texto, self.marcos)
        return vistas.referencias(propio, otro)

    @rx.var(deps=["comparar", *DEPS_CONFIG], auto_deps=False)
    def columnas_config(self) -> list[vistas.ColumnaVista]:
        """Tabla paso a paso de la configuración."""
        config = self._config()
        propio = calculos.simular_bits(self.texto, self.marcos, config)
        otro = calculos.simular_base(self.comparar, self.texto, self.marcos)
        return vistas.columnas(propio, config, otro)

    @rx.var(deps=["comparar", *DEPS_SECUENCIA], auto_deps=False)
    def columnas_comparacion(self) -> list[vistas.ColumnaVista]:
        """Tabla paso a paso del algoritmo de comparación."""
        return vistas.columnas(calculos.simular_base(self.comparar, self.texto, self.marcos), None)

    @rx.var(deps=["marcos"], auto_deps=False)
    def filas_marcos(self) -> list[str]:
        """Etiquetas de las filas de la tabla (una por marco)."""
        return [f"Marco {i + 1}" for i in range(self.marcos)]

    @rx.var(deps=["comparar", *DEPS_CONFIG], auto_deps=False)
    def resumen(self) -> vistas.ResumenVista:
        """Resumen final contra la comparación y el Óptimo."""
        propio = calculos.simular_bits(self.texto, self.marcos, self._config())
        otro = calculos.simular_base(self.comparar, self.texto, self.marcos)
        optimo = calculos.simular_base("optimo", self.texto, self.marcos)
        return vistas.resumen(propio, otro, optimo)

    # ------------------------------------------------------- secuencia

    @rx.event
    def elegir_fuente(self, clave: str) -> None:
        """Carga una secuencia precargada o genera una aleatoria."""
        if clave == FUENTE_ALEATORIA:
            self.generar_otra()
            return
        if clave == FUENTE_PROPIA:
            self.fuente = FUENTE_PROPIA
            return
        for item in PRECARGADAS:
            if item.clave == clave:
                self._poner_texto(item.texto, item.clave)

    @rx.event
    def enviar_secuencia(self, datos: dict[str, str]) -> None:
        """Valida la secuencia escrita y la carga si es correcta."""
        try:
            texto = a_texto(parsear(datos.get("secuencia", "")))
        except ErrorSecuencia as error:
            self.error = str(error)
            return
        if texto == self.texto:
            self.error = ""
            return
        fuente = next((item.clave for item in PRECARGADAS if item.texto == texto), FUENTE_PROPIA)
        self._poner_texto(texto, fuente)

    @rx.event
    def generar_otra(self) -> None:
        """Genera una secuencia nueva con localidad (el mismo generador de la validación)."""
        self.semilla += 1
        self._poner_texto(a_texto(generar_con_localidad(self.semilla)), FUENTE_ALEATORIA)

    @rx.event
    def set_marcos(self, valor: str) -> None:
        """Cambia el número de marcos (1 a 8)."""
        numero = int(valor)
        if MARCOS_MINIMOS <= numero <= MARCOS_MAXIMOS:
            self.marcos = numero
            self.paso = min(self.paso, self._total())

    # ------------------------------------------------------- configuración

    @rx.event
    def set_historia(self, valor: str) -> None:
        """Bits de historia (k)."""
        self.historia = int(valor)

    @rx.event
    def set_contador(self, valor: str) -> None:
        """Bits del contador de uso."""
        self.contador = int(valor)

    @rx.event
    def set_envejecimiento(self, valor: str) -> None:
        """Periodo de envejecimiento (0 lo apaga)."""
        self.envejecimiento = int(valor)

    @rx.event
    def set_orden(self, valor: str) -> None:
        """Orden de la cascada."""
        self.orden = OrdenReglas(valor).value

    @rx.event
    def alternar_m(self, activo: bool) -> None:
        """Activa el bit de modificada."""
        self.usa_m = activo

    @rx.event
    def alternar_p(self, activo: bool) -> None:
        """Activa el bit de fijada."""
        self.usa_p = activo

    @rx.event
    def alternar_fijada(self, pagina: int) -> None:
        """Fija o suelta una página."""
        if pagina in self.fijadas:
            self.fijadas = [p for p in self.fijadas if p != pagina]
        else:
            self.fijadas = sorted([*self.fijadas, pagina])

    @rx.event
    def aplicar_preset(self, clave: str) -> None:
        """Carga una configuración con nombre."""
        for item in presets.todos():
            if item.clave == clave:
                self._poner_config(item.config)
                self.fijadas = []

    @rx.event
    def set_comparar(self, clave: str) -> None:
        """Algoritmo contra el que se compara."""
        if clave in COMPARACIONES:
            self.comparar = clave

    @rx.event
    def cargar_en_laboratorio(self, historia: int, contador: int, envejecimiento: int | str, orden: str):
        """Abre el laboratorio con una configuración del explorador o de la validación."""
        self._poner_config(ConfigBits(int(historia), int(contador), int(envejecimiento), OrdenReglas(orden)))
        self.usa_m = False
        self.usa_p = False
        self.paso = 0
        self.reproduciendo = False
        return rx.redirect(RUTA_LABORATORIO)

    # ------------------------------------------------------- reproducción

    @rx.event
    def ir_a(self, paso: int) -> None:
        """Salta a un paso (tocando el bus de referencias)."""
        self.reproduciendo = False
        self.paso = max(0, min(paso, self._total()))

    @rx.event
    def anterior(self) -> None:
        """Paso anterior."""
        self.reproduciendo = False
        self.paso = max(0, self.paso - 1)

    @rx.event
    def siguiente(self) -> None:
        """Paso siguiente."""
        self.reproduciendo = False
        self.paso = min(self._total(), self.paso + 1)

    @rx.event
    def al_inicio(self) -> None:
        """Vuelve a la memoria vacía."""
        self.reproduciendo = False
        self.paso = 0

    @rx.event
    def set_velocidad(self, valor: str) -> None:
        """Velocidad de reproducción."""
        if valor in VELOCIDADES:
            self.velocidad = valor

    @rx.event
    def alternar_reproduccion(self):
        """Reproduce o pausa."""
        if self.reproduciendo:
            self.reproduciendo = False
            return None
        return EstadoApp.reproducir

    @rx.event(background=True)
    async def reproducir(self) -> None:
        """Avanza un paso cada cierto tiempo; solo corre una reproducción a la vez."""
        async with self:
            self._ejecucion += 1
            mia = self._ejecucion
            if self.paso >= self._total():
                self.paso = 0
            self.reproduciendo = True
        while True:
            async with self:
                if not self.reproduciendo or self._ejecucion != mia:
                    return
                self.paso += 1
                if self.paso >= self._total():
                    self.reproduciendo = False
                    return
                espera = SEGUNDOS_POR_PASO / float(self.velocidad)
            await asyncio.sleep(espera)

    @rx.event
    def exportar_csv(self):
        """Descarga las dos tablas paso a paso en CSV."""
        config = self._config()
        propio = calculos.simular_bits(self.texto, self.marcos, config)
        otro = calculos.simular_base(self.comparar, self.texto, self.marcos)
        return rx.download(data=vistas.csv_tabla(propio, config, otro), filename="tabla_paso_a_paso.csv")
