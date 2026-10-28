# Laboratorio de reemplazo de páginas

Aplicación web en Reflex para el trabajo de memoria virtual: FIFO mejorado con
**bits adicionales de referencia** (historia, contador de uso, envejecimiento, bit
de modificada y bit de fijada), comparado contra FIFO, la segunda oportunidad del
profesor, LRU y el Óptimo.

- **Laboratorio:** arma tu combinación de bits, mira el paso a paso animado sobre una
  placa de memoria y compáralo contra el algoritmo original.
- **Explorador:** prueba todas las combinaciones en tu secuencia, con ranking y mapa de calor.
- **Marcos:** gráfica de fallos de 1 a 10 marcos con la anomalía de Belady marcada.
- **Validación:** la configuración recomendada se elige con 500 secuencias y se mide con
  otras 500, para que no esté hecha a la medida de una sola.

## Instalación

Requiere Python 3.11 o superior. Reflex descarga Node/Bun la primera vez que corre.

```bash
python -m venv .venv
source .venv/bin/activate          # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Cómo correr

```bash
reflex run
```

Abre <http://localhost:3000>. La primera vez tarda un poco porque instala el frontend.

## Pruebas

```bash
pip install -r requirements-dev.txt
pytest          # 93 pruebas: valores de la sección 10 y tablas del Excel del profesor
ruff check .    # estilo
```

Las pruebas comparan celda por celda las hojas del Excel del profesor (Óptimo, FIFO con 3 y
4 marcos, Belady, LRU, MRU y la segunda oportunidad con bit y puntero), además de la traza
10.2 de la propuesta paso a paso.

`core/` es Python puro (no importa Reflex), así que las pruebas no necesitan el frontend.
La validación (5 s) se guarda en `laboratorio_paginas/datos/validacion.json`; si borras
ese archivo, la app la vuelve a calcular la primera vez que la necesita.

## Estructura

```
laboratorio_paginas/
├── core/            # motor determinista, sin Reflex
│   ├── algoritmos/  # optimo, fifo, lru, mru, segunda_oportunidad, fifo_bits
│   ├── secuencias.py, explorador.py, validacion.py, metricas.py, presets.py
├── estado/          # un State por pantalla y las vistas (dataclasses para la UI)
├── componentes/     # placa, chip, bus, cascada, tabla, marcador, panel de configuración…
├── paginas/         # inicio, laboratorio, explorador, marcos, validacion
└── estilos/         # constantes de tema
assets/
├── tokens.css       # colores, tipografía y espaciado
├── componentes.css  # estilos de la interfaz
├── animaciones.css  # keyframes y transiciones (y su versión con movimiento reducido)
├── atajos.js        # espacio, ← y → en el laboratorio
└── fuentes/         # IBM Plex servida desde la app (funciona sin internet)
```

## Decisiones sobre las definiciones

- **Segunda oportunidad:** mientras se llenan los marcos libres el puntero se queda en el
  marco 1, como en la hoja del profesor. Es equivalente a "el puntero queda en el siguiente
  marco": al llenar el último marco libre, el siguiente es justamente el 1.
- **Escrituras a disco:** se cuentan en todos los algoritmos (una página escrita siempre hay
  que guardarla al sacarla). El bit M solo cambia la decisión de cuál sacar.
- **Combinaciones equivalentes:** el explorador agrupa las que dan el mismo resultado en
  cualquier secuencia (sin historia no hay ventana ni recencia; sin regla de uso el contador
  y el envejecimiento no influyen; ventana justo antes de recencia sobra). Una prueba revisa
  que de verdad den lo mismo en 32 secuencias y con 2, 3 y 4 marcos. Quedan 126.

## Decisiones de diseño

### Idea

La memoria es un **módulo de RAM visto en un banco de pruebas**. Los marcos son
zócalos, las páginas son chips, los bits son LEDs y la memoria virtual es el disco, al
que se llega por el conector de borde del módulo (los "dedos" dorados de una RAM) a
través de pistas de cobre. Todo lo que se ve en la placa significa algo del algoritmo.

### Colores

| Token | Hex | Uso |
|---|---|---|
| Máscara de soldadura | `#0F3D2E` | Fondo de la página |
| Sustrato | `#0A2E22` | Zonas hundidas: bus de referencias, disco, celdas de tabla |
| Placa elevada | `#16503C` | Paneles y la placa de memoria |
| Cobre | `#C8823D` | Pistas, bordes de zócalos, acento (nunca texto pequeño) |
| Cobre para texto | `#E8A867` | Enlaces y texto en cobre (5,9:1 sobre la máscara, 4,6:1 sobre la placa) |
| Serigrafía | `#F0EEE3` | Texto (10,4:1 sobre la máscara, 8:1 sobre la placa) |
| Serigrafía tenue | `#A9BFB2` | Texto secundario (4,8:1 sobre la placa) |
| LED encendido | `#FFB627` | Bit en 1 |
| Acierto | `#5BC8E8` | Relleno con texto oscuro (7,6:1) |
| Fallo | `#F25C54` | Relleno con texto oscuro del sustrato (4,5:1) |
| Encapsulado | `#1A1E1C` | Cuerpo negro de los chips |

Ajustes contra la propuesta inicial, por contraste AA: el cobre `#C8823D` da 3:1 sobre la
placa, así que solo se usa en líneas y formas; para texto en cobre agregué `#E8A867`. El
rojo de fallo y el azul de acierto se usan como **rellenos con texto oscuro**, nunca como
color de texto sobre verde.

### Tipografía

- **IBM Plex Sans Condensed** (400, 500, 600) para toda la interfaz y los títulos: tiene
  el aire de una hoja de datos de un componente.
- **IBM Plex Mono** solo para bits, registros y la secuencia, donde el ancho fijo alinea
  columnas de bits.
- Escala (Bringhurst, base 16 px): 12 · 14 · 16 · 18 · 21 · 24 · 30 · 36 · 48. Texto
  corrido a 16/24, líneas de menos de 75 caracteres.

### Layout del laboratorio

```
┌──────────────────────────────────────────────────────────────────────────┐
│ Laboratorio de páginas        Inicio  Laboratorio  Explorador  Marcos  … │
├──────────────────────────────────────────────────────────────────────────┤
│ Bus  7 0 1 2 0 3 [0] 4 2 3 0 3 2 1 2 0      |◀  ◀  Reproducir  ▶  1×    │
├───────────────┬───────────────────────────────────────┬──────────────────┤
│ Secuencia     │  ┊      ┊      ┊   pulso de señal     │ Marcador (7 seg.)│
│ Configuración │ ┌────┐ ┌────┐ ┌────┐                  │  Tuya   FIFO     │
│ presets       │ │ 2  │ │ 0  │ │ 3  │  chips con LEDs  │   05     07      │
│ k, C, env.    │ │●○○○│ │●○●○│ │○●○○│  de H y puntos C │                  │
│ orden, M, P   │ └─┬──┘ └─┬──┘ └─┬──┘                  │ Decisión         │
│ costo: 6 bits │ ══╧══════╧══════╧══ pistas de cobre   │ cascada animada  │
│ Comparar con  │ ▮▮▮▮▮▮ Disco (conector de borde) ▮▮▮▮ │ "Sale la 3: …"   │
│               │ placa compacta de la comparación      │                  │
├───────────────┴───────────────────────────────────────┴──────────────────┤
│ Tabla paso a paso (estilo del Excel): tu configuración                   │
│ conectores «fallo evitado» / «fallo perdido» alineados por columna       │
│ Tabla paso a paso: algoritmo de comparación                              │
│ Resumen final                                              Exportar CSV  │
└──────────────────────────────────────────────────────────────────────────┘
```

Texto alineado a la izquierda; números de tablas a la derecha con cifras tabulares. En
celular la placa se apila: los zócalos quedan en columna y el disco al final.

### Principios

1. **La audacia va en un solo lugar: la placa.** Todo lo demás es serigrafía sobria:
   contornos finos, sin sombras, sin tarjetas, sin degradados.
2. **Cada forma significa algo.** Contorno de serigrafía = zona funcional; cobre = por
   donde viajan los datos; LED = bit; dígitos de 7 segmentos = contadores.
3. **Solo se mueve lo que cambió.** El registro de historia se corre en todos los chips
   a la vez; en un acierto solo destella un chip; en un fallo viaja la víctima.
4. **Nunca solo color.** Acierto es un círculo y dice "Acierto"; fallo es un cuadrado y
   dice "Fallo"; los LEDs encendidos están rellenos y los apagados son anillos, y debajo
   va el registro en binario.
5. **Honestidad.** Los casos donde la mejora pierde se muestran igual de visibles que
   donde gana, y "mejor para esta secuencia" nunca se confunde con "recomendada".

### Revisión contra lo genérico

- *Paneles como tarjetas redondeadas con sombra* → la página es una sola placa; las zonas
  se separan con contornos de serigrafía de 1 px y radio de 2 px, como en un PCB.
- *Estadística grande con degradado en el inicio* → el inicio es una carrera en vivo entre
  FIFO y la propuesta, con marcadores de 7 segmentos.
- *Monoespaciada para etiquetas pequeñas* → los designadores de zócalo (M1, M2…) y las
  etiquetas van en Plex Sans Condensed; la Mono queda solo para bits y secuencias.
- *Textos tipo "A · B · C" y flechas en botones* → las configuraciones se describen con
  comas ("k 3, C 2 bits, envejecimiento cada 8") y los botones dicen la acción.
- *Contadores con fichas que giran* → los marcadores son displays de 7 segmentos, que es
  lo que tendría un banco de pruebas real.
- Antes de cerrar quité un adorno: el contorno punteado alrededor de cada zócalo repetía
  el borde del chip. Ahora solo aparece cuando el marco está libre, que es cuando dice algo.

## Valores verificados

Con la secuencia del profesor y 3 marcos: Óptimo 8, FIFO 12, LRU 11, MRU 14, segunda
oportunidad 12 y la propuesta del grupo (k 4, C 2 bits, envejecimiento cada 8) **9**.
La recomendada por validación es k 3, C 2 bits, envejecimiento cada 8 (5 bits): en las
500 secuencias de prueba promedia 15,99 fallos con 3 marcos, contra 16,85 de FIFO.
