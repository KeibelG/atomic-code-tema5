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
# Ejemplo práctico de un Árbol de Sintaxis Abstracta (AST). Un AST representa
# la estructura jerárquica de un programa conservando solo lo que importa para
# interpretarlo o compilarlo: se descartan paréntesis, punto y coma y demás
# símbolos puramente sintácticos, y cada nodo interno es directamente un
# constructor del lenguaje (una suma, una comparación, un if, una asignación).
# Esto lo distingue del árbol de análisis (parse tree), que sí conserva cada
# regla de la gramática aplicada durante la derivación.
#
# El programa tokeniza y parsea (recursivo descendente, escrito a mano) DOS
# entradas de ejemplo y muestra el AST resultante como árbol en consola:
#
#   Ejemplo A) una expresión aritmética:      (3 + 4) * 2 - 1
#   Ejemplo B) una sentencia de control:      if x > 3 then print(x) else print(0)
#
# Gramática de expresiones (Ejemplo A, y también las subexpresiones dentro
# del Ejemplo B):
#   expr   ::= term (('+' | '-') term)*
#   term   ::= factor (('*' | '/') factor)*
#   factor ::= NUM | ID | '(' expr ')'
#
# Gramática de sentencia (Ejemplo B):
#   stmt   ::= 'if' cond 'then' stmt 'else' stmt
#            | 'print' '(' expr ')'
#            | ID '=' expr
#   cond   ::= expr ('>' | '<' | '==' | '!=' | '>=' | '<=') expr
# ---------------------------------------------------------------------------

import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


# ===========================================================================
#           1) NODO DEL AST Y SU IMPRESIÓN COMO ÁRBOL
# ===========================================================================
class Nodo:
    """Un nodo del AST: una etiqueta (el constructor del lenguaje), un valor
    opcional (el lexema, solo en hojas u operadores) y sus hijos."""

    def __init__(self, etiqueta, hijos=None, valor=None):
        self.etiqueta = etiqueta
        self.hijos = hijos or []
        self.valor = valor

    def texto(self):
        return self.etiqueta if self.valor is None else f"{self.etiqueta} ({self.valor})"


def imprimir_arbol(nodo):
    print(nodo.texto())
    _imprimir_hijos(nodo.hijos, "")


def _imprimir_hijos(hijos, prefijo):
    for i, hijo in enumerate(hijos):
        ultimo = i == len(hijos) - 1
        conector = "`-- " if ultimo else "|-- "
        print(prefijo + conector + hijo.texto())
        extension = "    " if ultimo else "|   "
        _imprimir_hijos(hijo.hijos, prefijo + extension)


# ===========================================================================
#           2) TOKENIZADOR (compartido por ambos ejemplos)
# ===========================================================================
PALABRAS_CLAVE = {"if": "IF", "then": "THEN", "else": "ELSE", "print": "PRINT"}

ESPECIFICACION_TOKENS = [
    ("NUM", r"\d+"),
    ("ID", r"[A-Za-z_][A-Za-z0-9_]*"),
    ("IGUALIGUAL", r"=="),
    ("DISTINTO", r"!="),
    ("MAYORIGUAL", r">="),
    ("MENORIGUAL", r"<="),
    ("IGUAL", r"="),
    ("MAYOR", r">"),
    ("MENOR", r"<"),
    ("MAS", r"\+"),
    ("MENOS", r"-"),
    ("POR", r"\*"),
    ("ENTRE", r"/"),
    ("PAR_ABRE", r"\("),
    ("PAR_CIERRA", r"\)"),
    ("ESPACIO", r"[ \t]+"),
]
REGEX_TOKENS = "|".join(f"(?P<{nombre}>{patron})" for nombre, patron in ESPECIFICACION_TOKENS)


def tokenizar(texto):
    tokens = []
    for coincidencia in re.finditer(REGEX_TOKENS, texto):
        tipo = coincidencia.lastgroup
        valor = coincidencia.group(tipo)
        if tipo == "ESPACIO":
            continue
        if tipo == "ID" and valor in PALABRAS_CLAVE:
            tipo = PALABRAS_CLAVE[valor]
        tokens.append((tipo, valor))
    return tokens


# ===========================================================================
#           3) PARSER RECURSIVO DESCENDENTE -> CONSTRUYE EL AST
# ===========================================================================
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def actual(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else ("EOF", "")

    def avanzar(self):
        tok = self.actual()
        self.pos += 1
        return tok

    def esperar(self, tipo):
        tok = self.actual()
        if tok[0] != tipo:
            raise SyntaxError(f"se esperaba {tipo} pero se encontro {tok[0]} ({tok[1]!r})")
        return self.avanzar()

    def esperar_alguno(self, *tipos):
        tok = self.actual()
        if tok[0] not in tipos:
            raise SyntaxError(f"se esperaba uno de {tipos} pero se encontro {tok[0]} ({tok[1]!r})")
        return self.avanzar()

    # -- Gramática de expresiones (Ejemplo A) --------------------------------
    def expr(self):
        nodo = self.term()
        while self.actual()[0] in ("MAS", "MENOS"):
            op = self.avanzar()
            nodo = Nodo("BinOp", [nodo, self.term()], valor=op[1])
        return nodo

    def term(self):
        nodo = self.factor()
        while self.actual()[0] in ("POR", "ENTRE"):
            op = self.avanzar()
            nodo = Nodo("BinOp", [nodo, self.factor()], valor=op[1])
        return nodo

    def factor(self):
        tipo, valor = self.actual()
        if tipo == "NUM":
            self.avanzar()
            return Nodo("Num", valor=valor)
        if tipo == "ID":
            self.avanzar()
            return Nodo("Id", valor=valor)
        if tipo == "PAR_ABRE":
            self.avanzar()
            nodo = self.expr()
            self.esperar("PAR_CIERRA")
            return nodo
        raise SyntaxError(f"factor inesperado: {tipo} ({valor!r})")

    # -- Gramática de sentencia (Ejemplo B), reutiliza expr() ----------------
    def stmt(self):
        tipo, _ = self.actual()
        if tipo == "IF":
            self.avanzar()
            condicion = self.cond()
            self.esperar("THEN")
            rama_si = self.stmt()
            self.esperar("ELSE")
            rama_no = self.stmt()
            return Nodo("If", [condicion, rama_si, rama_no])
        if tipo == "PRINT":
            self.avanzar()
            self.esperar("PAR_ABRE")
            argumento = self.expr()
            self.esperar("PAR_CIERRA")
            return Nodo("Print", [argumento])
        if tipo == "ID":
            nombre = self.avanzar()
            self.esperar("IGUAL")
            valor = self.expr()
            return Nodo("Asignacion", [valor], valor=nombre[1])
        raise SyntaxError(f"sentencia inesperada: {tipo}")

    def cond(self):
        izquierda = self.expr()
        op = self.esperar_alguno("MAYOR", "MENOR", "IGUALIGUAL", "DISTINTO", "MAYORIGUAL", "MENORIGUAL")
        derecha = self.expr()
        return Nodo("Comparacion", [izquierda, derecha], valor=op[1])


# ===========================================================================
#           4) EJECUCIÓN DE LOS DOS EJEMPLOS
# ===========================================================================
def ejecutar():
    print("===========================================================")
    print("     Ejemplo práctico de Árbol de Sintaxis Abstracta (AST)")
    print("                  Equipo: Atomic Code")
    print("===========================================================\n")

    print("-----------------------------------------------------------")
    print(" Ejemplo A) Expresión aritmética")
    print("-----------------------------------------------------------")
    entrada_a = "(3 + 4) * 2 - 1"
    tokens_a = tokenizar(entrada_a)
    ast_a = Parser(tokens_a).expr()
    print(f"Entrada:  {entrada_a}")
    print(f"Tokens:   {tokens_a}\n")
    print("AST:")
    imprimir_arbol(ast_a)

    print("\n-----------------------------------------------------------")
    print(" Ejemplo B) Sentencia de control (if / else)")
    print("-----------------------------------------------------------")
    entrada_b = "if x > 3 then print(x) else print(0)"
    tokens_b = tokenizar(entrada_b)
    ast_b = Parser(tokens_b).stmt()
    print(f"Entrada:  {entrada_b}")
    print(f"Tokens:   {tokens_b}\n")
    print("AST:")
    imprimir_arbol(ast_b)


if __name__ == "__main__":
    ejecutar()
