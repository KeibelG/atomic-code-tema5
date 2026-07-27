# Lenguaje:   Python 3
# Asignatura: Lenguajes y compiladores
# Equipo:     Atomic Code
#             Segmentando el código, construyendo la lógica
#
# Integrantes:
#   - Victor Vargas    C.I: 30.697.219
#   - Keibel Guilarte  C.I: 28.726.605
#   - Oriana Márquez   C.I: 31.354.299
#   - Jeanny Monagas   C.I: 30.857.471
#
# ---------------------------------------------------------------------------
#                           DESCRIPCIÓN
# ---------------------------------------------------------------------------
# Utilidades compartidas entre el parser LL (ll_parser.py) y el parser LR
# (lr_parser.py) del lenguaje L = expresiones aritméticas con +, -, *, /,
# paréntesis y enteros. Ambos parsers deben reconocer exactamente el mismo
# lenguaje L y construir el mismo AST para una misma cadena de entrada, así
# que comparten aquí: 1) el nodo de AST y su impresión como árbol, 2) el
# tokenizador (léxico de L), y 3) una función para comparar dos AST y
# verificar que dos derivaciones distintas (descendente vs ascendente)
# produjeron el mismo resultado.
# ---------------------------------------------------------------------------

import re


# ===========================================================================
#           1) NODO DEL AST Y SU IMPRESIÓN COMO ÁRBOL
# ===========================================================================
class Nodo:
    def __init__(self, etiqueta, hijos=None, valor=None):
        self.etiqueta = etiqueta
        self.hijos = hijos or []
        self.valor = valor

    def texto(self):
        return self.etiqueta if self.valor is None else f"{self.etiqueta} ({self.valor})"


def imprimir_arbol(nodo, prefijo=""):
    if prefijo == "":
        print(nodo.texto())
    _imprimir_hijos(nodo.hijos, prefijo)


def _imprimir_hijos(hijos, prefijo):
    for i, hijo in enumerate(hijos):
        ultimo = i == len(hijos) - 1
        conector = "`-- " if ultimo else "|-- "
        print(prefijo + conector + hijo.texto())
        extension = "    " if ultimo else "|   "
        _imprimir_hijos(hijo.hijos, prefijo + extension)


def arboles_iguales(a, b):
    """Compara dos AST estructuralmente (misma etiqueta, mismo valor, mismos
    hijos en el mismo orden). Se usa para demostrar que el parser LL y el
    parser LR, pese a construir el árbol en direcciones opuestas, terminan
    en el mismo AST para la misma cadena del lenguaje L."""
    if a.etiqueta != b.etiqueta or a.valor != b.valor or len(a.hijos) != len(b.hijos):
        return False
    return all(arboles_iguales(x, y) for x, y in zip(a.hijos, b.hijos))


# ===========================================================================
#           2) LÉXICO DE L: expresiones aritméticas (+, -, *, /, (, ), num)
# ===========================================================================
ESPECIFICACION_TOKENS = [
    ("NUM", r"\d+"),
    ("MAS", r"\+"),
    ("MENOS", r"-"),
    ("POR", r"\*"),
    ("ENTRE", r"/"),
    ("PAR_ABRE", r"\("),
    ("PAR_CIERRA", r"\)"),
    ("ESPACIO", r"[ \t]+"),
]
REGEX_TOKENS = "|".join(f"(?P<{nombre}>{patron})" for nombre, patron in ESPECIFICACION_TOKENS)

# Traduce el tipo de token del lexer al símbolo terminal de la gramática de L.
TERMINAL_DE_TOKEN = {
    "NUM": "num", "MAS": "+", "MENOS": "-", "POR": "*", "ENTRE": "/",
    "PAR_ABRE": "(", "PAR_CIERRA": ")", "FIN": "$",
}


def tokenizar(texto):
    """Tokeniza una cadena de L y agrega al final el marcador de fin '$'."""
    tokens = []
    for coincidencia in re.finditer(REGEX_TOKENS, texto):
        tipo = coincidencia.lastgroup
        valor = coincidencia.group(tipo)
        if tipo == "ESPACIO":
            continue
        tokens.append((tipo, valor))
    tokens.append(("FIN", "$"))
    return tokens
