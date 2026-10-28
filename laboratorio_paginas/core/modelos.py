"""Modelos inmutables que comparten todos los algoritmos.

Nada de este módulo depende de Reflex: son dataclasses congeladas que la
interfaz solo lee.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

HISTORIAS_PERMITIDAS: tuple[int, ...] = (0, 2, 3, 4, 8)
CONTADORES_PERMITIDOS: tuple[int, ...] = (0, 1, 2, 3)
ENVEJECIMIENTOS_PERMITIDOS: tuple[int, ...] = (0, 4, 8)
"""0 significa envejecimiento apagado; 4 y 8 son el periodo N."""


class Regla(StrEnum):
    """Reglas de la cascada de salida."""

    VENTANA = "ventana"
    USO = "uso"
    RECENCIA = "recencia"
    MODIFICADA = "modificada"
    FIFO = "fifo"


NOMBRES_REGLA: dict[Regla, str] = {
    Regla.VENTANA: "ventana",
    Regla.USO: "uso",
    Regla.RECENCIA: "recencia",
    Regla.MODIFICADA: "modificada",
    Regla.FIFO: "FIFO",
}


class OrdenReglas(StrEnum):
    """Órdenes de la cascada que puede elegir el usuario."""

    PROPUESTA = "propuesta"
    USO_PRIMERO = "uso_primero"
    RECENCIA_PRIMERO = "recencia_primero"
    SOLO_VENTANA = "solo_ventana"


NOMBRES_ORDEN: dict[OrdenReglas, str] = {
    OrdenReglas.PROPUESTA: "Propuesta",
    OrdenReglas.USO_PRIMERO: "Uso primero",
    OrdenReglas.RECENCIA_PRIMERO: "Recencia primero",
    OrdenReglas.SOLO_VENTANA: "Solo ventana",
}

REGLAS_POR_ORDEN: dict[OrdenReglas, tuple[Regla, ...]] = {
    OrdenReglas.PROPUESTA: (Regla.VENTANA, Regla.USO, Regla.RECENCIA, Regla.MODIFICADA, Regla.FIFO),
    OrdenReglas.USO_PRIMERO: (Regla.USO, Regla.RECENCIA, Regla.MODIFICADA, Regla.FIFO),
    OrdenReglas.RECENCIA_PRIMERO: (Regla.RECENCIA, Regla.USO, Regla.MODIFICADA, Regla.FIFO),
    OrdenReglas.SOLO_VENTANA: (Regla.VENTANA, Regla.MODIFICADA, Regla.FIFO),
}


@dataclass(frozen=True)
class ConfigBits:
    """Configuración de los bits adicionales de FIFO.

    Atributos:
        historia: bits del registro de corrimiento H (k).
        contador: bits del contador de uso C (0 apaga la regla de uso).
        envejecimiento: periodo N para dividir C entre 2; 0 lo apaga.
        orden: orden de la cascada de salida.
        modificada: si se usa el bit M.
        fijada: si se usa el bit P.
        paginas_fijadas: páginas que llevan P = 1 cuando el bit está activo.
    """

    historia: int = 0
    contador: int = 0
    envejecimiento: int = 0
    orden: OrdenReglas = OrdenReglas.PROPUESTA
    modificada: bool = False
    fijada: bool = False
    paginas_fijadas: frozenset[int] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if self.historia not in HISTORIAS_PERMITIDAS:
            raise ValueError(f"La historia debe ser uno de {HISTORIAS_PERMITIDAS} bits.")
        if self.contador not in CONTADORES_PERMITIDOS:
            raise ValueError(f"El contador debe tener uno de {CONTADORES_PERMITIDOS} bits.")
        if self.envejecimiento not in ENVEJECIMIENTOS_PERMITIDOS:
            raise ValueError(f"El envejecimiento debe ser uno de {ENVEJECIMIENTOS_PERMITIDOS}.")

    @property
    def contador_maximo(self) -> int:
        """Valor de saturación de C."""
        return (1 << self.contador) - 1

    @property
    def costo_bits(self) -> int:
        """Bits por marco: k + bits de C + M + P."""
        return self.historia + self.contador + int(self.modificada) + int(self.fijada)

    @property
    def reglas(self) -> tuple[Regla, ...]:
        """Reglas que de verdad se aplican con esta configuración, en orden."""
        activas: list[Regla] = []
        for regla in REGLAS_POR_ORDEN[self.orden]:
            if regla in (Regla.VENTANA, Regla.RECENCIA) and self.historia == 0:
                continue
            if regla is Regla.USO and self.contador == 0:
                continue
            if regla is Regla.MODIFICADA and not self.modificada:
                continue
            activas.append(regla)
        return tuple(activas)

    @property
    def envejecimiento_activo(self) -> bool:
        """El envejecimiento solo hace algo si hay contador."""
        return self.envejecimiento > 0 and self.contador > 0

    def describir(self) -> str:
        """Resumen corto: «k 4, C 2 bits, envejecimiento cada 8, Propuesta»."""
        partes = [f"k {self.historia}", f"C {self.contador} bit" + ("" if self.contador == 1 else "s")]
        partes.append(f"envejecimiento cada {self.envejecimiento}" if self.envejecimiento else "sin envejecimiento")
        partes.append(NOMBRES_ORDEN[self.orden])
        if self.modificada:
            partes.append("con M")
        if self.fijada:
            partes.append("con P")
        return ", ".join(partes)


class Evento(StrEnum):
    """Qué le pasó a un marco en un paso."""

    NINGUNO = "ninguno"
    ENTRADA = "entrada"
    REEMPLAZO = "reemplazo"
    ACIERTO = "acierto"


@dataclass(frozen=True)
class Referencia:
    """Una referencia a memoria: página y si es escritura."""

    pagina: int
    escritura: bool = False

    def __str__(self) -> str:
        return f"{self.pagina}w" if self.escritura else str(self.pagina)


@dataclass(frozen=True)
class EstadoMarco:
    """Foto de un marco después de procesar un paso."""

    indice: int
    pagina: int | None = None
    historia: str = ""
    contador: int = 0
    modificada: bool = False
    fijada: bool = False
    llegada: int = 0
    ultimo_uso: int = 0
    bit_r: int | None = None
    puntero: bool = False
    evento: Evento = Evento.NINGUNO
    salio: int | None = None

    @property
    def libre(self) -> bool:
        """True si el marco está vacío."""
        return self.pagina is None


@dataclass(frozen=True)
class Candidata:
    """Datos de una página candidata a salir, como se veían al decidir."""

    pagina: int
    marco: int
    historia: str
    contador: int
    modificada: bool
    llegada: int


@dataclass(frozen=True)
class PasoCascada:
    """Una regla aplicada: candidatas antes y después, y por qué."""

    regla: Regla
    antes: tuple[int, ...]
    despues: tuple[int, ...]
    razon: str

    @property
    def filtro(self) -> bool:
        """True si la regla descartó al menos una candidata."""
        return len(self.despues) < len(self.antes)


@dataclass(frozen=True)
class Decision:
    """Explicación completa de por qué salió una página."""

    victima: int
    marco: int
    candidatas: tuple[Candidata, ...]
    fijadas_excluidas: tuple[int, ...]
    pasos: tuple[PasoCascada, ...]
    regla_decisiva: Regla | None
    frase: str


@dataclass(frozen=True)
class Paso:
    """Instantánea inmutable de la simulación después del paso `indice`."""

    indice: int
    referencia: Referencia
    acierto: bool
    marcos: tuple[EstadoMarco, ...]
    victima: int | None
    marco_afectado: int | None
    decision: Decision | None
    fallos_acumulados: int
    escritura_disco: bool
    escrituras_acumuladas: int
    envejecimiento: bool

    @property
    def fallo(self) -> bool:
        """True si la referencia no estaba en memoria."""
        return not self.acierto


@dataclass(frozen=True)
class Resultado:
    """Resultado de simular una secuencia con un algoritmo."""

    algoritmo: str
    numero_marcos: int
    pasos: tuple[Paso, ...]

    @property
    def fallos(self) -> int:
        """Fallos totales, incluidas las cargas iniciales."""
        return self.pasos[-1].fallos_acumulados if self.pasos else 0

    @property
    def aciertos(self) -> int:
        """Referencias que ya estaban en memoria."""
        return len(self.pasos) - self.fallos

    @property
    def escrituras_disco(self) -> int:
        """Páginas modificadas que hubo que guardar al sacarlas."""
        return self.pasos[-1].escrituras_acumuladas if self.pasos else 0

    @property
    def tasa_fallos(self) -> float:
        """Porcentaje de fallos sobre el total de referencias."""
        return 100.0 * self.fallos / len(self.pasos) if self.pasos else 0.0
