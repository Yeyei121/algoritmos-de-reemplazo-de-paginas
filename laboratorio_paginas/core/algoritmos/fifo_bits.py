"""FIFO con bits adicionales de referencia y cascada de salida explicada.

Orden de actualización en cada paso i (1, 2, 3…):

1. Acierto: C = min(C + 1, Cmax); si es escritura, M = 1.
2. Fallo: si hay marco libre se carga ahí; si no, la cascada elige la víctima
   y la página nueva entra en su marco con H = 0, C = 0 y M según la referencia.
3. Corrimiento de historia (si k > 0): H = (H >> 1) | (1 << (k - 1)) para la
   página referenciada y H = H >> 1 para las demás.
4. Envejecimiento (si está activo e i % N == 0): C = C >> 1 para todas.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from laboratorio_paginas.core.algoritmos.base import crear_paso, lista_paginas
from laboratorio_paginas.core.modelos import (
    Candidata,
    ConfigBits,
    Decision,
    EstadoMarco,
    Evento,
    Paso,
    PasoCascada,
    Regla,
    Resultado,
)
from laboratorio_paginas.core.secuencias import Secuencia

FRASE_REGLA: dict[Regla, str] = {
    Regla.VENTANA: "la regla de ventana",
    Regla.USO: "la regla de uso",
    Regla.RECENCIA: "la regla de recencia",
    Regla.MODIFICADA: "la regla del bit M",
    Regla.FIFO: "la regla FIFO",
}


@dataclass
class _Memoria:
    """Estado mutable de la placa durante la simulación (listas paralelas)."""

    marcos: int
    pagina: list[int | None] = field(init=False)
    historia: list[int] = field(init=False)
    contador: list[int] = field(init=False)
    modificada: list[bool] = field(init=False)
    llegada: list[int] = field(init=False)
    ubicacion: dict[int, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.pagina = [None] * self.marcos
        self.historia = [0] * self.marcos
        self.contador = [0] * self.marcos
        self.modificada = [False] * self.marcos
        self.llegada = [0] * self.marcos

    def cargar(self, marco: int, pagina: int, escritura: bool, paso: int) -> None:
        """Pone una página nueva en el marco con sus bits en cero."""
        anterior = self.pagina[marco]
        if anterior is not None:
            del self.ubicacion[anterior]
        self.pagina[marco] = pagina
        self.historia[marco] = 0
        self.contador[marco] = 0
        self.modificada[marco] = escritura
        self.llegada[marco] = paso
        self.ubicacion[pagina] = marco


@dataclass(frozen=True)
class _Filtro:
    """Una regla aplicada, en índices de marco (versión interna)."""

    regla: Regla
    antes: tuple[int, ...]
    despues: tuple[int, ...]


def _cascada(
    candidatas: list[int], reglas: tuple[Regla, ...], mem: _Memoria, registrar: bool
) -> tuple[int, list[_Filtro]]:
    """Filtra candidatas regla por regla hasta que queda una."""
    filtros: list[_Filtro] = []
    for regla in reglas:
        if len(candidatas) == 1:
            break
        antes = candidatas
        if regla is Regla.VENTANA:
            sin_uso = [m for m in candidatas if mem.historia[m] == 0]
            candidatas = sin_uso or candidatas
        elif regla is Regla.USO:
            minimo = min(mem.contador[m] for m in candidatas)
            candidatas = [m for m in candidatas if mem.contador[m] == minimo]
        elif regla is Regla.RECENCIA:
            minimo = min(mem.historia[m] for m in candidatas)
            candidatas = [m for m in candidatas if mem.historia[m] == minimo]
        elif regla is Regla.MODIFICADA:
            limpias = [m for m in candidatas if not mem.modificada[m]]
            candidatas = limpias or candidatas
        else:
            candidatas = [min(candidatas, key=lambda m: mem.llegada[m])]
        if registrar:
            filtros.append(_Filtro(regla, tuple(antes), tuple(candidatas)))
    return candidatas[0], filtros


def _candidatas_iniciales(mem: _Memoria, config: ConfigBits) -> tuple[list[int], list[int]]:
    """Todos los marcos, quitando los fijados salvo que todos lo estén."""
    todos = list(range(mem.marcos))
    if not config.fijada or not config.paginas_fijadas:
        return todos, []
    libres = [m for m in todos if mem.pagina[m] not in config.paginas_fijadas]
    if not libres:
        return todos, []
    fijados = [m for m in todos if m not in libres]
    return libres, fijados


@dataclass(frozen=True)
class FifoBits:
    """FIFO mejorado con historia, contador, envejecimiento, M y P configurables."""

    config: ConfigBits
    nombre: str = "FIFO con bits"

    def simular(self, secuencia: Secuencia, marcos: int) -> Resultado:
        """Simula y devuelve todas las instantáneas con sus explicaciones."""
        pasos = _motor(self.config, secuencia, marcos, registrar=True)
        return Resultado(self.nombre, marcos, tuple(pasos))  # type: ignore[arg-type]

    def contar_fallos(self, secuencia: Secuencia, marcos: int) -> int:
        """Versión rápida para el explorador y la validación: solo cuenta fallos."""
        return _motor(self.config, secuencia, marcos, registrar=False)  # type: ignore[return-value]


def contar_fallos(config: ConfigBits, secuencia: Secuencia, marcos: int) -> int:
    """Atajo funcional de FifoBits(config).contar_fallos."""
    return _motor(config, secuencia, marcos, registrar=False)  # type: ignore[return-value]


def _motor(config: ConfigBits, secuencia: Secuencia, marcos: int, registrar: bool) -> list[Paso] | int:
    """Bucle principal. Con registrar=False solo cuenta fallos (mucho más rápido)."""
    mem = _Memoria(marcos)
    reglas = config.reglas
    k = config.historia
    bit_entrada = 1 << (k - 1) if k else 0
    cmax = config.contador_maximo
    periodo = config.envejecimiento if config.envejecimiento_activo else 0
    pasos: list[Paso] = []
    fallos = 0
    escrituras = 0
    for posicion, ref in enumerate(secuencia):
        indice = posicion + 1
        marco = mem.ubicacion.get(ref.pagina)
        acierto = marco is not None
        victima: int | None = None
        decision: Decision | None = None
        escritura_disco = False
        if marco is not None:
            if mem.contador[marco] < cmax:
                mem.contador[marco] += 1
            mem.modificada[marco] = mem.modificada[marco] or ref.escritura
        else:
            fallos += 1
            if len(mem.ubicacion) < marcos:
                marco = mem.pagina.index(None)
            else:
                candidatas, fijados = _candidatas_iniciales(mem, config)
                marco, filtros = _cascada(candidatas, reglas, mem, registrar)
                victima = mem.pagina[marco]
                escritura_disco = mem.modificada[marco]
                escrituras += int(escritura_disco)
                if registrar:
                    decision = _explicar(mem, config, candidatas, fijados, filtros, marco)
            mem.cargar(marco, ref.pagina, ref.escritura, indice)
        if k:
            for m in range(marcos):
                if mem.pagina[m] is not None:
                    mem.historia[m] = (mem.historia[m] >> 1) | (bit_entrada if m == marco else 0)
        envejecio = bool(periodo) and indice % periodo == 0
        if envejecio:
            for m in range(marcos):
                mem.contador[m] >>= 1
        if registrar:
            pasos.append(
                crear_paso(
                    indice,
                    ref,
                    acierto,
                    _foto(mem, config, marco, acierto, victima),
                    victima,
                    marco,
                    decision,
                    fallos,
                    escritura_disco,
                    escrituras,
                    envejecio,
                )
            )
    return pasos if registrar else fallos


def _historia_texto(valor: int, k: int) -> str:
    return format(valor, f"0{k}b") if k else ""


def _foto(mem: _Memoria, config: ConfigBits, marco: int, acierto: bool, victima: int | None) -> tuple[EstadoMarco, ...]:
    fotos: list[EstadoMarco] = []
    for m in range(mem.marcos):
        pagina = mem.pagina[m]
        evento = Evento.NINGUNO
        if m == marco:
            evento = Evento.ACIERTO if acierto else (Evento.REEMPLAZO if victima is not None else Evento.ENTRADA)
        fotos.append(
            EstadoMarco(
                indice=m,
                pagina=pagina,
                historia=_historia_texto(mem.historia[m], config.historia) if pagina is not None else "",
                contador=mem.contador[m],
                modificada=mem.modificada[m],
                fijada=config.fijada and pagina in config.paginas_fijadas,
                llegada=mem.llegada[m],
                evento=evento,
                salio=victima if m == marco else None,
            )
        )
    return tuple(fotos)


# ---------------------------------------------------------------- explicación


def _explicar(
    mem: _Memoria,
    config: ConfigBits,
    candidatas: list[int],
    fijados: list[int],
    filtros: list[_Filtro],
    marco: int,
) -> Decision:
    """Convierte los filtros internos en una explicación legible."""
    k = config.historia
    datos = {
        m: Candidata(
            pagina=mem.pagina[m],  # type: ignore[arg-type]
            marco=m,
            historia=_historia_texto(mem.historia[m], k),
            contador=mem.contador[m],
            modificada=mem.modificada[m],
            llegada=mem.llegada[m],
        )
        for m in candidatas
    }
    pasos = tuple(
        PasoCascada(
            regla=f.regla,
            antes=tuple(datos[m].pagina for m in f.antes),
            despues=tuple(datos[m].pagina for m in f.despues),
            razon=_razon_paso(f, datos, k),
        )
        for f in filtros
    )
    victima = datos[marco].pagina
    excluidas = tuple(mem.pagina[m] for m in fijados)
    frase = _frase(victima, filtros, datos, k)
    if excluidas:
        verbo = "no participó porque está fijada" if len(excluidas) == 1 else "no participaron porque están fijadas"
        frase += f" {lista_paginas(excluidas).capitalize()} {verbo}."  # type: ignore[arg-type]
    return Decision(
        victima=victima,
        marco=marco,
        candidatas=tuple(datos[m] for m in candidatas),
        fijadas_excluidas=excluidas,  # type: ignore[arg-type]
        pasos=pasos,
        regla_decisiva=filtros[-1].regla if filtros else None,
        frase=frase,
    )


def _paginas(marcos: tuple[int, ...], datos: dict[int, Candidata]) -> str:
    return lista_paginas([datos[m].pagina for m in marcos])


def _razon_paso(filtro: _Filtro, datos: dict[int, Candidata], k: int) -> str:
    """Frase corta para el panel de decisión: qué hizo esta regla."""
    quedan = _paginas(filtro.despues, datos)
    sigue = "sigue" if len(filtro.despues) == 1 else "siguen"
    primero = datos[filtro.despues[0]]
    if filtro.regla is Regla.VENTANA:
        if len(filtro.despues) == len(filtro.antes) and primero.historia != "0" * k:
            return f"Todas se usaron en las últimas {k} iteraciones, así que siguen todas."
        return f"Sin uso en las últimas {k} iteraciones (H = {'0' * k}): {sigue} {quedan}."
    if filtro.regla is Regla.USO:
        if len(filtro.despues) == len(filtro.antes):
            return f"Todas tienen C = {primero.contador}, así que siguen todas."
        return f"Menor contador (C = {primero.contador}): {sigue} {quedan}."
    if filtro.regla is Regla.RECENCIA:
        if len(filtro.despues) == len(filtro.antes):
            return f"Todas tienen H = {primero.historia}, así que siguen todas."
        return f"Historia más baja ({primero.historia}): {sigue} {quedan}."
    if filtro.regla is Regla.MODIFICADA:
        if len(filtro.despues) == len(filtro.antes):
            estado = "modificadas" if primero.modificada else "sin modificar"
            return f"Todas están {estado}, así que siguen todas."
        return f"Sin modificar (M = 0), no hay que escribirlas en disco: {sigue} {quedan}."
    return f"La que llegó primero (paso {primero.llegada}): {sigue} {quedan}."


def _razon_decisiva(regla: Regla, victima: Candidata, otras: list[Candidata], k: int) -> str:
    """Por qué la víctima ganó en la regla que decidió."""
    if regla is Regla.VENTANA:
        return f"era la única sin uso en las últimas {k} iteraciones (H = {victima.historia})"
    if regla is Regla.USO:
        otro = min(c.contador for c in otras)
        return f"tenía el contador más bajo (C = {victima.contador} < {otro})"
    if regla is Regla.RECENCIA:
        otra = min(otras, key=lambda c: c.historia).historia
        return f"tenía la historia más baja ({victima.historia} < {otra})"
    if regla is Regla.MODIFICADA:
        return "era la única sin modificar (M = 0), así que no hay que escribirla en disco"
    return f"era la que llevaba más tiempo en memoria (entró en el paso {victima.llegada})"


def _detalle_empate(previos: list[_Filtro], empatadas: list[Candidata]) -> str:
    """Lo que tenían en común las empatadas, por ejemplo « (C = 1)»."""
    aplicadas = {f.regla for f in previos}
    partes: list[str] = []
    historias = {c.historia for c in empatadas}
    if aplicadas & {Regla.VENTANA, Regla.RECENCIA} and len(historias) == 1:
        partes.append(f"H = {empatadas[0].historia}")
    if Regla.USO in aplicadas:
        partes.append(f"C = {empatadas[0].contador}")
    if Regla.MODIFICADA in aplicadas and len({c.modificada for c in empatadas}) == 1:
        partes.append(f"M = {int(empatadas[0].modificada)}")
    return f" ({', '.join(partes)})" if partes else ""


def _frase(victima: int, filtros: list[_Filtro], datos: dict[int, Candidata], k: int) -> str:
    """Frase completa en español: «Sale la 3: después de la regla de uso…»."""
    if not filtros:
        return f"Sale la {victima}: es la única que no está fijada."
    decisivo = filtros[-1]
    empatadas = [datos[m] for m in decisivo.antes]
    marco_victima = decisivo.despues[0]
    otras = [c for c in empatadas if c.marco != marco_victima]
    razon = _razon_decisiva(decisivo.regla, datos[marco_victima], otras, k)
    previos = filtros[:-1]
    reductores = [f for f in previos if len(f.despues) < len(f.antes)]
    if not reductores:
        return f"Sale la {victima}: {razon}."
    nombre = FRASE_REGLA[reductores[-1].regla]
    lista = lista_paginas(sorted(c.pagina for c in empatadas))
    detalle = _detalle_empate(previos, empatadas)
    return f"Sale la {victima}: después de {nombre} empataban {lista}{detalle}, y la {victima} {razon}."
