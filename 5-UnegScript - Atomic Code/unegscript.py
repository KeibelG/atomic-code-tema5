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
# Punto de entrada del asistente de programación híbrido "UnegScript"
# (Pregunta 5 del Tema 5): une el lexer híbrido (lexer_hibrido.py), el
# parser recursivo descendente (parser_recursivo.py) y el motor de
# sugerencias (motor_ia_simulado.py).
#
# Corre el ejemplo de código con errores del enunciado:
#     pront x = 5; if x > 3 prnt(x) else prnt("no")
# y muestra exactamente lo que pide el punto 4) de la actividad:
#   1) Tokens corregidos
#   2) AST
#   3) Sugerencias IA (formato "Sugerencia: 'pront' -> 'print'")
#
# Uso: python unegscript.py                 (corre el ejemplo del enunciado)
#      python unegscript.py "otro codigo"   (corre un código arbitrario)
# ---------------------------------------------------------------------------

import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "1-AST - Atomic Code"))

from lexer_hibrido import lexer_hibrido
from parser_recursivo import parsear
from ast_ejemplo import imprimir_arbol

EJEMPLO_DEL_ENUNCIADO = 'pront x = 5; if x > 3 prnt(x) else prnt("no")'


def ejecutar_unegscript(codigo_fuente):
    print("=" * 63)
    print(" UnegScript - asistente de programación híbrido")
    print("            Equipo: Atomic Code")
    print("=" * 63)
    print(f"\nCódigo de entrada:\n  {codigo_fuente}\n")

    try:
        tokens, sugerencias_lexer = lexer_hibrido(codigo_fuente)
    except SyntaxError as error:
        print("-" * 63)
        print(" 1) Tokens corregidos")
        print("-" * 63)
        print(f"  Error léxico, no se pudo tokenizar por completo: {error}")
        print()
        return

    print("-" * 63)
    print(" 1) Tokens corregidos")
    print("-" * 63)
    for tipo, valor in tokens:
        print(f"  ({tipo}, {valor!r})")

    print("\n" + "-" * 63)
    print(" 2) AST")
    print("-" * 63)
    notas_parser = []
    try:
        ast, notas_parser = parsear(tokens)
        imprimir_arbol(ast)
    except SyntaxError as error:
        print(f"  No se pudo completar el AST: {error}")

    print("\n" + "-" * 63)
    print(" 3) Sugerencias IA")
    print("-" * 63)
    ya_mostradas = set()
    for sugerencia in sugerencias_lexer:
        clave = (sugerencia.original, sugerencia.corregido)
        if clave in ya_mostradas:
            continue
        ya_mostradas.add(clave)
        print(f"  Sugerencia: '{sugerencia.original}' -> '{sugerencia.corregido}'"
              f"   (confianza={sugerencia.confianza:.2f}, {sugerencia.fuente})")

    if notas_parser:
        print("\n  Notas adicionales del parser (recuperación de errores sintácticos):")
        for nota in notas_parser:
            print(f"    - {nota.contexto}")

    print()


if __name__ == "__main__":
    codigo = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else EJEMPLO_DEL_ENUNCIADO
    ejecutar_unegscript(codigo)
