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
# Parser recursivo descendente con lookahead(1) para UnegScript, que
# construye el AST (reutiliza el nodo/impresor de "1-AST - Atomic Code").
#
# Gramática:
#   programa   ::= stmt (';' stmt)* ';'?
#   stmt       ::= ID '=' expr
#              |  'if' cond stmt 'else' stmt
#              |  'print' '(' expr ')'
#   cond       ::= expr ('>' | '<' | '==' | '!=' | '>=' | '<=') expr
#   expr       ::= term (('+' | '-') term)*
#   term       ::= factor (('*' | '/') factor)*
#   factor     ::= NUM | STRING | ID | '(' expr ')'
#
# Cuando el token bajo el lookahead no encaja con la producción esperada, en
# vez de abortar de inmediato el parser CONSULTA al motor de IA
# (motor_ia_simulado.sugerir_reparacion_sintactica) para registrar una
# sugerencia legible, y aplica una recuperación de tipo "pánico" acotada: si
# 'print' no está seguido de '(', se asume que ese 'print' quedó mal ubicado
# (ruido léxico) y se descarta, reintentando la sentencia desde el token
# siguiente. Es la misma técnica que menciona la sección 4 del enunciado del
# tema ("panic o inserción de tokens faltantes").
# ---------------------------------------------------------------------------

import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "1-AST - Atomic Code"))
import motor_ia_simulado as ia
from ast_ejemplo import Nodo  # se reutiliza el nodo/impresor de árbol del punto 1

OPERADORES_COMPARACION = ("MAYOR", "MENOR", "IGUALIGUAL", "DISTINTO", "MAYORIGUAL", "MENORIGUAL")


class ParserUnegScript:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.notas_ia = []  # sugerencias de reparación sintáctica generadas durante el parseo

    def actual(self):
        return self.tokens[self.pos]

    def avanzar(self):
        tok = self.actual()
        self.pos += 1
        return tok

    def esperar(self, tipo, contexto=""):
        tok = self.actual()
        if tok[0] != tipo:
            sugerencia = ia.sugerir_reparacion_sintactica(tipo, tok, contexto)
            self.notas_ia.append(sugerencia)
            raise SyntaxError(f"se esperaba {tipo} pero se encontró {tok[0]} ({tok[1]!r}); {contexto}")
        return self.avanzar()

    # programa ::= stmt (';' stmt)* ';'?
    def programa(self):
        sentencias = [self.stmt()]
        while self.actual()[0] == "PUNTOYCOMA":
            self.avanzar()
            if self.actual()[0] == "FIN":
                break
            sentencias.append(self.stmt())
        self.esperar("FIN", contexto="al final del programa")
        return Nodo("Programa", sentencias)

    def stmt(self):
        tipo, _ = self.actual()

        if tipo == "KW_PRINT":
            self.avanzar()
            if self.actual()[0] != "PAR_ABRE":
                sugerencia = ia.sugerir_reparacion_sintactica(
                    "PAR_ABRE", self.actual(), contexto="justo después de 'print'"
                )
                self.notas_ia.append(sugerencia)
                # modo pánico acotado: el 'print' no encaja aquí, se descarta
                # como ruido y se reintenta la sentencia desde este punto.
                return self.stmt()
            self.avanzar()  # '('
            argumento = self.expr()
            self.esperar("PAR_CIERRA", contexto="cerrando el print(...)")
            return Nodo("Print", [argumento])

        if tipo == "KW_IF":
            self.avanzar()
            condicion = self.cond()
            rama_si = self.stmt()
            self.esperar("KW_ELSE", contexto="después de la rama 'si' del if")
            rama_no = self.stmt()
            return Nodo("If", [condicion, rama_si, rama_no])

        if tipo == "ID":
            nombre = self.avanzar()
            self.esperar("IGUAL", contexto=f"después del identificador '{nombre[1]}'")
            valor = self.expr()
            return Nodo("Asignacion", [valor], valor=nombre[1])

        sugerencia = ia.sugerir_reparacion_sintactica("inicio de sentencia", self.actual())
        self.notas_ia.append(sugerencia)
        raise SyntaxError(f"sentencia inesperada: {tipo}")

    def cond(self):
        izquierda = self.expr()
        tok = self.actual()
        if tok[0] not in OPERADORES_COMPARACION:
            sugerencia = ia.sugerir_reparacion_sintactica("operador de comparación", tok, contexto="en la condición del if")
            self.notas_ia.append(sugerencia)
            raise SyntaxError(f"se esperaba un operador de comparación, se encontró {tok[0]}")
        operador = self.avanzar()
        derecha = self.expr()
        return Nodo("Comparacion", [izquierda, derecha], valor=operador[1])

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
        if tipo == "STRING":
            self.avanzar()
            return Nodo("Str", valor=valor.strip('"'))
        if tipo == "ID":
            self.avanzar()
            return Nodo("Id", valor=valor)
        if tipo == "PAR_ABRE":
            self.avanzar()
            nodo = self.expr()
            self.esperar("PAR_CIERRA", contexto="cerrando la subexpresión")
            return nodo
        sugerencia = ia.sugerir_reparacion_sintactica("NUM, STRING, ID o '('", (tipo, valor))
        self.notas_ia.append(sugerencia)
        raise SyntaxError(f"factor inesperado: {tipo} ({valor!r})")


def parsear(tokens):
    parser = ParserUnegScript(tokens)
    ast = parser.programa()
    return ast, parser.notas_ia


if __name__ == "__main__":
    from lexer_hibrido import lexer_hibrido
    from ast_ejemplo import imprimir_arbol

    fuente = 'pront x=5; if x>3 prnt(x) else prnt("no")'
    tokens, sugerencias_lexer = lexer_hibrido(fuente)
    ast, notas_parser = parsear(tokens)

    print(f"Entrada: {fuente}\n")
    print("AST:")
    imprimir_arbol(ast)
    print("\nNotas del parser (consulta a IA por fallos sintácticos):")
    for nota in notas_parser:
        print(f"  {nota.contexto}")
