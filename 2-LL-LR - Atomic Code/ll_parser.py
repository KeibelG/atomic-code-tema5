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
# Analizador sintáctico LL(1) (descendente, recursivo, con derivación por la
# izquierda) para el lenguaje L = expresiones aritméticas con +, -, *, /,
# paréntesis y enteros.
#
# La gramática "natural" de las expresiones es recursiva por la izquierda
# (E -> E + T | E - T | T), y un LL(1) NO puede usarla tal cual: entraría en
# recursión infinita sin consumir entrada. Por eso se transforma a la forma
# equivalente sin recursión izquierda (técnica estándar de factorización):
#
#   E   ::= T E'
#   E'  ::= '+' T E'  |  '-' T E'  |  epsilon
#   T   ::= F T'
#   T'  ::= '*' F T'  |  '/' F T'  |  epsilon
#   F   ::= '(' E ')' |  num
#
# Cada no terminal es una función; el lookahead (1 token) alcanza para saber
# qué producción aplicar (no hay ambigüedad). E' y T' reciben el subárbol ya
# construido hacia su izquierda ("atributo heredado") para poder armar un
# AST asociativo a la izquierda pese a que la gramática ya no lo es.
# ---------------------------------------------------------------------------

import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ast_nodes import Nodo, tokenizar


class ParserLL:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.traza = []

    def actual(self):
        return self.tokens[self.pos]

    def avanzar(self):
        tok = self.actual()
        self.pos += 1
        return tok

    def esperar(self, tipo):
        tok = self.actual()
        if tok[0] != tipo:
            raise SyntaxError(f"LL: se esperaba {tipo} pero se encontro {tok[0]} ({tok[1]!r})")
        return self.avanzar()

    # E ::= T E'
    def E(self):
        self.traza.append("E -> T E'")
        return self.Ep(self.T())

    # E' ::= '+' T E' | '-' T E' | epsilon
    def Ep(self, heredado):
        tipo, val = self.actual()
        if tipo in ("MAS", "MENOS"):
            self.traza.append(f"E' -> '{val}' T E'")
            self.avanzar()
            nodo = Nodo("BinOp", [heredado, self.T()], valor=val)
            return self.Ep(nodo)
        self.traza.append("E' -> epsilon")
        return heredado

    # T ::= F T'
    def T(self):
        self.traza.append("T -> F T'")
        return self.Tp(self.F())

    # T' ::= '*' F T' | '/' F T' | epsilon
    def Tp(self, heredado):
        tipo, val = self.actual()
        if tipo in ("POR", "ENTRE"):
            self.traza.append(f"T' -> '{val}' F T'")
            self.avanzar()
            nodo = Nodo("BinOp", [heredado, self.F()], valor=val)
            return self.Tp(nodo)
        self.traza.append("T' -> epsilon")
        return heredado

    # F ::= '(' E ')' | num
    def F(self):
        tipo, val = self.actual()
        if tipo == "NUM":
            self.traza.append(f"F -> num({val})")
            self.avanzar()
            return Nodo("Num", valor=val)
        if tipo == "PAR_ABRE":
            self.traza.append("F -> ( E )")
            self.avanzar()
            nodo = self.E()
            self.esperar("PAR_CIERRA")
            return nodo
        raise SyntaxError(f"LL: factor inesperado: {tipo} ({val!r})")


def parsear_ll(texto):
    tokens = tokenizar(texto)
    parser = ParserLL(tokens)
    ast = parser.E()
    parser.esperar("FIN")
    return ast, parser.traza


if __name__ == "__main__":
    from ast_nodes import imprimir_arbol

    entrada = "(3 + 4) * 2 - 1"
    ast, traza = parsear_ll(entrada)
    print(f"Entrada: {entrada}\n")
    print("Traza de derivación (LL, por la izquierda):")
    for paso in traza:
        print("  " + paso)
    print("\nAST:")
    imprimir_arbol(ast)
