"""Vistas: dataclasses planas que la interfaz pinta tal cual.

Aquí no hay algoritmos: solo se traducen las instantáneas del motor a textos,
listas de LEDs y estados de animación.
"""

from __future__ import annotations

import dataclasses

from laboratorio_paginas.core.metricas import Diferencia, diferencias
from laboratorio_paginas.core.modelos import (
    NOMBRES_REGLA,
    ConfigBits,
    EstadoMarco,
    Evento,
    Paso,
    Resultado,
)

ENCENDIDO = "1"
APAGADO = "0"
LED_NUEVO = "nuevo"
LED_SE_APAGA = "se_apaga"


@dataclasses.dataclass
class ChipVista:
    """Un zócalo de la placa en el paso actual."""

    marco: int = 0
    designador: str = ""
    pagina: str = ""
    libre: bool = True
    evento: str = Evento.NINGUNO.value
    salio: str = ""
    historia: str = ""
    historia_previa: str = ""
    """H antes del corrimiento (se ve hasta que los LEDs se corren)."""
    leds: list[str] = dataclasses.field(default_factory=list)
    """LEDs de H después del corrimiento: «1» o «0»."""
    led_entrante: str = ""
    led_caido: str = ""
    puntos: list[str] = dataclasses.field(default_factory=list)
    """Puntos de C: «1», «0», «nuevo» (se encendió) o «se_apaga»."""
    contador: int = 0
    modificada: bool = False
    fijada: bool = False
    llegada: int = 0
    ultimo_uso: int = 0
    bit_r: str = ""
    puntero: bool = False
    candidata: bool = False
    escritura_disco: bool = False


@dataclasses.dataclass
class CandidataVista:
    """Una página dentro de una regla de la cascada."""

    pagina: str = ""
    detalle: str = ""
    sigue: bool = True


@dataclasses.dataclass
class ReglaVista:
    """Una regla aplicada en el paso actual."""

    nombre: str = ""
    razon: str = ""
    decidio: bool = False
    candidatas: list[CandidataVista] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class PasoVista:
    """Todo lo que la placa necesita para dibujar un paso."""

    indice: int = 0
    referencia: str = ""
    escritura: bool = False
    acierto: bool = False
    inicial: bool = True
    victima: str = ""
    marco_afectado: int = -1
    frase: str = ""
    resumen: str = ""
    reglas: list[ReglaVista] = dataclasses.field(default_factory=list)
    fijadas_excluidas: str = ""
    fallos: int = 0
    escrituras: int = 0
    escritura_disco: bool = False
    envejecimiento: bool = False
    chips: list[ChipVista] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class CeldaVista:
    """Una celda de la tabla al estilo del profesor."""

    pagina: str = ""
    detalle: str = ""
    cambio: bool = False
    evento: str = Evento.NINGUNO.value
    puntero: bool = False


@dataclasses.dataclass
class ColumnaVista:
    """Una columna (un paso) de la tabla al estilo del profesor."""

    indice: int = 0
    referencia: str = ""
    celdas: list[CeldaVista] = dataclasses.field(default_factory=list)
    sale: str = ""
    fallo: bool = False
    diferencia: str = Diferencia.IGUAL.value


@dataclasses.dataclass
class ReferenciaVista:
    """Una referencia del bus de la parte superior."""

    indice: int = 0
    texto: str = ""
    escritura: bool = False
    fallo: bool = False
    diferencia: str = Diferencia.IGUAL.value


# ----------------------------------------------------------------- placa


def _bits(texto: str) -> list[str]:
    return list(texto)


def _puntos(antes: int, despues: int, maximo: int) -> list[str]:
    puntos: list[str] = []
    for i in range(maximo):
        if i < despues:
            puntos.append(LED_NUEVO if i >= antes else ENCENDIDO)
        else:
            puntos.append(LED_SE_APAGA if i < antes else APAGADO)
    return puntos


def _misma_pagina(anterior: EstadoMarco | None, actual: EstadoMarco) -> bool:
    return (
        anterior is not None
        and anterior.pagina == actual.pagina
        and actual.evento
        not in (
            Evento.ENTRADA,
            Evento.REEMPLAZO,
        )
    )


def _chip(
    actual: EstadoMarco,
    anterior: EstadoMarco | None,
    config: ConfigBits | None,
    candidatas: set[int],
    escritura_disco: bool,
) -> ChipVista:
    k = config.historia if config else 0
    maximo = config.contador_maximo if config else 0
    sigue = _misma_pagina(anterior, actual)
    historia_previa = anterior.historia if sigue and anterior else "0" * k
    contador_previo = anterior.contador if sigue and anterior else 0
    return ChipVista(
        marco=actual.indice,
        designador=f"M{actual.indice + 1}",
        pagina="" if actual.pagina is None else str(actual.pagina),
        libre=actual.pagina is None,
        evento=actual.evento.value,
        salio="" if actual.salio is None else str(actual.salio),
        historia=actual.historia,
        historia_previa=historia_previa if actual.pagina is not None else "",
        leds=_bits(actual.historia),
        led_entrante=actual.historia[:1],
        led_caido=historia_previa[-1:] if k else "",
        puntos=_puntos(contador_previo, actual.contador, maximo) if actual.pagina is not None else [],
        contador=actual.contador,
        modificada=actual.modificada,
        fijada=actual.fijada,
        llegada=actual.llegada,
        ultimo_uso=actual.ultimo_uso,
        bit_r="" if actual.bit_r is None else str(actual.bit_r),
        puntero=actual.puntero,
        candidata=actual.indice in candidatas,
        escritura_disco=escritura_disco and actual.evento is Evento.REEMPLAZO,
    )


def _detalle_candidata(historia: str, contador: int, modificada: bool, config: ConfigBits) -> str:
    partes: list[str] = []
    if config.historia:
        partes.append(f"H {historia}")
    if config.contador:
        partes.append(f"C {contador}")
    if config.modificada:
        partes.append(f"M {int(modificada)}")
    return ", ".join(partes)


def _reglas(paso: Paso, config: ConfigBits | None) -> list[ReglaVista]:
    decision = paso.decision
    if decision is None or config is None or not decision.pasos:
        return []
    datos = {c.pagina: c for c in decision.candidatas}
    reglas: list[ReglaVista] = []
    ultimo = len(decision.pasos) - 1
    for i, regla in enumerate(decision.pasos):
        candidatas = [
            CandidataVista(
                pagina=str(p),
                detalle=_detalle_candidata(datos[p].historia, datos[p].contador, datos[p].modificada, config),
                sigue=p in regla.despues,
            )
            for p in regla.antes
        ]
        reglas.append(
            ReglaVista(
                nombre=NOMBRES_REGLA[regla.regla].capitalize() if regla.regla.value != "fifo" else "FIFO",
                razon=regla.razon,
                decidio=i == ultimo,
                candidatas=candidatas,
            )
        )
    return reglas


def _resumen_paso(paso: Paso) -> str:
    ref = paso.referencia
    if paso.acierto:
        marco = next(m for m in paso.marcos if m.pagina == ref.pagina)
        return f"Acierto: la {ref.pagina} ya estaba en el marco M{marco.indice + 1}."
    if paso.victima is None:
        return f"Fallo: la {ref.pagina} entra en el marco libre M{(paso.marco_afectado or 0) + 1}."
    return f"Fallo: la {ref.pagina} no está en memoria y hay que sacar una página."


def paso_inicial(marcos: int) -> PasoVista:
    """Placa vacía antes del primer paso."""
    return PasoVista(
        chips=[ChipVista(marco=i, designador=f"M{i + 1}") for i in range(marcos)],
        resumen="Memoria vacía. Pulsa Reproducir o Siguiente paso.",
    )


def pasos_vista(resultado: Resultado, config: ConfigBits | None) -> list[PasoVista]:
    """Todas las instantáneas traducidas para la placa, empezando por la vacía."""
    vistas = [paso_inicial(resultado.numero_marcos)]
    anterior: Paso | None = None
    for paso in resultado.pasos:
        candidatas = {c.marco for c in paso.decision.candidatas} if paso.decision else set()
        chips = [
            _chip(m, anterior.marcos[m.indice] if anterior else None, config, candidatas, paso.escritura_disco)
            for m in paso.marcos
        ]
        decision = paso.decision
        vistas.append(
            PasoVista(
                indice=paso.indice,
                referencia=str(paso.referencia.pagina),
                escritura=paso.referencia.escritura,
                acierto=paso.acierto,
                inicial=False,
                victima="" if paso.victima is None else str(paso.victima),
                marco_afectado=-1 if paso.marco_afectado is None else paso.marco_afectado,
                frase=decision.frase if decision else "",
                resumen=_resumen_paso(paso),
                reglas=_reglas(paso, config),
                fijadas_excluidas=", ".join(str(p) for p in decision.fijadas_excluidas) if decision else "",
                fallos=paso.fallos_acumulados,
                escrituras=paso.escrituras_acumuladas,
                escritura_disco=paso.escritura_disco,
                envejecimiento=paso.envejecimiento,
                chips=chips,
            )
        )
        anterior = paso
    return vistas


# ----------------------------------------------------------------- tabla


def _detalle_celda(marco: EstadoMarco, config: ConfigBits | None) -> str:
    if marco.pagina is None:
        return ""
    if marco.bit_r is not None:
        return f"B {marco.bit_r}"
    if config is None:
        return ""
    partes: list[str] = []
    if config.historia:
        partes.append(marco.historia)
    if config.contador:
        partes.append(f"C{marco.contador}")
    if config.modificada and marco.modificada:
        partes.append("M")
    return " ".join(partes)


def columnas(
    resultado: Resultado, config: ConfigBits | None, comparacion: Resultado | None = None
) -> list[ColumnaVista]:
    """Columnas de la tabla al estilo del profesor (una por paso)."""
    cambios = diferencias(resultado, comparacion) if comparacion else ()
    salida: list[ColumnaVista] = []
    anterior: Paso | None = None
    for i, paso in enumerate(resultado.pasos):
        celdas = []
        for marco in paso.marcos:
            previo = anterior.marcos[marco.indice] if anterior else None
            texto = "" if marco.pagina is None else str(marco.pagina)
            detalle = _detalle_celda(marco, config)
            if previo is None:
                cambio = True
            else:
                texto_previo = "" if previo.pagina is None else str(previo.pagina)
                cambio = texto != texto_previo or detalle != _detalle_celda(previo, config)
            celdas.append(
                CeldaVista(
                    pagina=texto, detalle=detalle, cambio=cambio, evento=marco.evento.value, puntero=marco.puntero
                )
            )
        salida.append(
            ColumnaVista(
                indice=paso.indice,
                referencia=str(paso.referencia),
                celdas=celdas,
                sale="" if paso.victima is None else str(paso.victima),
                fallo=paso.fallo,
                diferencia=cambios[i].value if cambios else Diferencia.IGUAL.value,
            )
        )
        anterior = paso
    return salida


def referencias(resultado: Resultado, comparacion: Resultado | None) -> list[ReferenciaVista]:
    """Referencias del bus con su resultado (para marcar fallos ya ocurridos)."""
    cambios = diferencias(resultado, comparacion) if comparacion else ()
    return [
        ReferenciaVista(
            indice=paso.indice,
            texto=str(paso.referencia.pagina),
            escritura=paso.referencia.escritura,
            fallo=paso.fallo,
            diferencia=cambios[i].value if cambios else Diferencia.IGUAL.value,
        )
        for i, paso in enumerate(resultado.pasos)
    ]


def csv_tabla(resultado: Resultado, config: ConfigBits | None, comparacion: Resultado) -> str:
    """Las dos tablas en CSV, una debajo de la otra, como en el Excel."""
    filas: list[list[str]] = []
    for nombre, res, cfg in ((resultado.algoritmo, resultado, config), (comparacion.algoritmo, comparacion, None)):
        filas.append([nombre, *[str(p.referencia) for p in res.pasos]])
        for m in range(res.numero_marcos):
            celdas = []
            for paso in res.pasos:
                marco = paso.marcos[m]
                detalle = _detalle_celda(marco, cfg)
                texto = "" if marco.pagina is None else str(marco.pagina)
                celdas.append(f"{texto} ({detalle})" if detalle else texto)
            filas.append([f"Marco {m + 1}", *celdas])
        filas.append(["Sale", *["" if p.victima is None else str(p.victima) for p in res.pasos]])
        filas.append(["Fallo", *["Fallo" if p.fallo else "" for p in res.pasos]])
        filas.append([f"Fallos: {res.fallos}"])
        filas.append([])
    return "\n".join(",".join(_csv(c) for c in fila) for fila in filas) + "\n"


def _csv(valor: str) -> str:
    return f'"{valor}"' if "," in valor or " " in valor else valor


@dataclasses.dataclass
class ResumenVista:
    """Números del resumen final."""

    fallos: int = 0
    aciertos: int = 0
    total: int = 0
    tasa: str = ""
    nombre_comparacion: str = ""
    fallos_comparacion: int = 0
    diferencia_comparacion: str = ""
    fallos_optimo: int = 0
    diferencia_optimo: str = ""
    escrituras: int = 0
    escrituras_comparacion: int = 0
    evitados: int = 0
    perdidos: int = 0
    veredicto: str = ""


def con_signo(valor: int) -> str:
    """«−3», «+1» o «0», con el signo menos tipográfico."""
    if valor > 0:
        return f"+{valor}"
    if valor < 0:
        return f"−{abs(valor)}"
    return "0"


def porcentaje(valor: float) -> str:
    """«56,3 %» con coma decimal."""
    return f"{valor:.1f}".replace(".", ",") + " %"


def decimal(valor: float, cifras: int = 2) -> str:
    """Número con coma decimal."""
    return f"{valor:.{cifras}f}".replace(".", ",")


def digitos(valor: int) -> list[str]:
    """Dos dígitos para el marcador de 7 segmentos; el cero a la izquierda va apagado."""
    decenas, unidades = divmod(max(valor, 0), 10)
    return ["" if decenas == 0 else str(decenas % 10), str(unidades)]


def resumen(propio: Resultado, comparacion: Resultado, optimo: Resultado) -> ResumenVista:
    """Resumen final de la configuración contra la comparación y el Óptimo."""
    from laboratorio_paginas.core.metricas import resumir

    datos = resumir(propio, comparacion, optimo)
    if datos.diferencia_comparacion < 0:
        veredicto = f"Tu configuración evita {-datos.diferencia_comparacion} fallos frente a {comparacion.algoritmo}."
    elif datos.diferencia_comparacion > 0:
        veredicto = (
            f"Con esta secuencia tu configuración hace {datos.diferencia_comparacion} fallos más "
            f"que {comparacion.algoritmo}."
        )
    else:
        veredicto = f"Empata con {comparacion.algoritmo} en esta secuencia."
    return ResumenVista(
        fallos=datos.fallos,
        aciertos=datos.aciertos,
        total=len(propio.pasos),
        tasa=porcentaje(datos.tasa),
        nombre_comparacion=comparacion.algoritmo,
        fallos_comparacion=comparacion.fallos,
        diferencia_comparacion=con_signo(datos.diferencia_comparacion),
        fallos_optimo=optimo.fallos,
        diferencia_optimo=con_signo(datos.diferencia_optimo),
        escrituras=datos.escrituras,
        escrituras_comparacion=comparacion.escrituras_disco,
        evitados=datos.evitados,
        perdidos=datos.perdidos,
        veredicto=veredicto,
    )
