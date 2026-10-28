"""Tablas copiadas del Excel del profesor (Algoritmos_reemplazo_de_p_ginas_1_1.xlsx).

Cada cadena es una fila (un marco) y cada posición es un paso; «-» es marco vacío.
La fila «sale» dice qué página salió en cada paso.
"""

PROFESOR = "7 0 1 2 0 3 0 4 2 3 0 3 2 1 2 0"
BELADY = "1 2 3 4 1 2 5 1 2 3 4 5"

TABLAS = {
    ("Óptimo", PROFESOR, 3): (
        ["7 7 7 2 2 2 2 2 2 2 2 2 2 2 2 2", "- 0 0 0 0 0 0 4 4 4 0 0 0 0 0 0", "- - 1 1 1 3 3 3 3 3 3 3 3 1 1 1"],
        "- - - 7 - 1 - 0 - - 4 - - 3 - -",
    ),
    ("FIFO", PROFESOR, 3): (
        ["7 7 7 2 2 2 2 4 4 4 0 0 0 0 0 0", "- 0 0 0 0 3 3 3 2 2 2 2 2 1 1 1", "- - 1 1 1 1 0 0 0 3 3 3 3 3 2 2"],
        "- - - 7 - 0 1 2 3 0 4 - - 2 3 -",
    ),
    ("FIFO", PROFESOR, 4): (
        [
            "7 7 7 7 7 3 3 3 3 3 3 3 3 3 2 2",
            "- 0 0 0 0 0 0 4 4 4 4 4 4 4 4 4",
            "- - 1 1 1 1 1 1 1 1 0 0 0 0 0 0",
            "- - - 2 2 2 2 2 2 2 2 2 2 1 1 1",
        ],
        None,
    ),
    ("FIFO", BELADY, 3): (
        ["1 1 1 4 4 4 5 5 5 5 5 5", "- 2 2 2 1 1 1 1 1 3 3 3", "- - 3 3 3 2 2 2 2 2 4 4"],
        None,
    ),
    ("FIFO", BELADY, 4): (
        ["1 1 1 1 1 1 5 5 5 5 4 4", "- 2 2 2 2 2 2 1 1 1 1 5", "- - 3 3 3 3 3 3 2 2 2 2", "- - - 4 4 4 4 4 4 3 3 3"],
        None,
    ),
    ("LRU", PROFESOR, 3): (
        ["7 7 7 2 2 2 2 4 4 4 0 0 0 1 1 1", "- 0 0 0 0 0 0 0 0 3 3 3 3 3 3 0", "- - 1 1 1 3 3 3 2 2 2 2 2 2 2 2"],
        "- - - 7 - 1 - 2 3 0 4 - - 0 - 3",
    ),
    ("MRU", PROFESOR, 3): (
        ["7 7 7 7 7 7 7 7 7 7 7 7 7 7 7 7", "- 0 0 0 0 3 0 4 4 4 4 4 4 4 4 4", "- - 1 2 2 2 2 2 2 3 0 3 2 1 2 0"],
        "- - - 1 - 0 3 0 - 2 3 0 3 2 1 2",
    ),
}

# Hoja «Fifo Mejorado - 2da Oport»: por paso, (página, bit R, tiene puntero) de cada marco.
SEGUNDA_OPORTUNIDAD = [
    [
        (7, 1, "*"),
        (7, 1, "*"),
        (7, 1, "*"),
        (2, 1, None),
        (2, 1, None),
        (2, 1, "*"),
        (2, 1, "*"),
        (4, 1, None),
        (4, 1, None),
        (4, 1, None),
        (4, 0, "*"),
        (3, 1, None),
        (3, 1, None),
        (3, 0, None),
        (3, 0, "*"),
        (0, 1, None),
    ],
    [
        (None, None, None),
        (0, 1, None),
        (0, 1, None),
        (0, 0, "*"),
        (0, 1, "*"),
        (0, 0, None),
        (0, 1, None),
        (0, 0, "*"),
        (2, 1, None),
        (2, 1, None),
        (2, 0, None),
        (2, 0, "*"),
        (2, 1, "*"),
        (1, 1, None),
        (1, 1, None),
        (1, 1, "*"),
    ],
    [
        (None, None, None),
        (None, None, None),
        (1, 1, None),
        (1, 0, None),
        (1, 0, None),
        (3, 1, None),
        (3, 1, None),
        (3, 0, None),
        (3, 0, "*"),
        (3, 1, "*"),
        (0, 1, None),
        (0, 1, None),
        (0, 1, None),
        (0, 0, "*"),
        (2, 1, None),
        (2, 1, None),
    ],
]
SEGUNDA_OPORTUNIDAD_SALE = "- - - 7 - 1 - 2 0 - 3 4 - 2 0 3"
