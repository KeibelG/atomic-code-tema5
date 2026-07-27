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
# Comparación entre el análisis LL (ll_parser.py) y el análisis LR
# (lr_parser.py) para el mismo lenguaje L = expresiones aritméticas.
#
# Corre un mismo conjunto de cadenas de prueba por AMBOS parsers (uno
# descendente por la izquierda, otro ascendente desplazar-reducir) y verifica
# que, pese a construir el árbol en direcciones opuestas y con gramáticas
# distintas (una sin recursión izquierda para LL, la natural con recursión
# izquierda para LR), ambos reconocen exactamente el mismo lenguaje L y
# producen el mismo AST. También reporta un caso que NO pertenece a L, para
# mostrar que ambos analizadores lo rechazan por igual.
# ---------------------------------------------------------------------------

import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ast_nodes import imprimir_arbol, arboles_iguales
from ll_parser import parsear_ll
from lr_parser import parsear_lr, GeneradorLR, PRODUCCIONES_L, SIMBOLO_INICIAL

CASOS_VALIDOS = [
    "3",
    "2 + 3 * 4",
    "(3 + 4) * 2 - 1",
    "10 - 2 - 3",
    "(1 + 2) * (3 + 4) / 7",
]
CASOS_INVALIDOS = [
    "3 + * 4",
    "(2 + 3",
]


def comparar(entrada, generador_lr):
    print("=" * 63)
    print(f" L = {entrada}")
    print("=" * 63)

    ast_ll, traza_ll = parsear_ll(entrada)
    print(f"\nLL(1) descendente: {len(traza_ll)} pasos de derivación.")
    print("AST (LL):")
    imprimir_arbol(ast_ll)

    ast_lr, traza_lr, _ = parsear_lr(entrada, generador_lr)
    print(f"\nLR (SLR(1)) ascendente: {len(traza_lr)} pasos de desplazar/reducir.")
    print("AST (LR):")
    imprimir_arbol(ast_lr)

    iguales = arboles_iguales(ast_ll, ast_lr)
    print(f"\n¿Mismo AST? {'SI - ambos analizadores reconocen el mismo lenguaje L' if iguales else 'NO (revisar)'}")
    print()
    return iguales


def ejecutar():
    print("###########################################################")
    print("   Comparación LL vs LR para el mismo lenguaje L")
    print("                Equipo: Atomic Code")
    print("###########################################################\n")

    generador_lr = GeneradorLR(PRODUCCIONES_L, SIMBOLO_INICIAL)
    print(f"Tabla SLR(1) construida: {len(generador_lr.estados)} estados, "
          f"{len(generador_lr.accion)} entradas ACTION, {len(generador_lr.ir)} entradas GOTO.\n")

    total = len(CASOS_VALIDOS)
    coinciden = 0
    for caso in CASOS_VALIDOS:
        if comparar(caso, generador_lr):
            coinciden += 1

    print("-" * 63)
    print(f"Resumen: {coinciden}/{total} cadenas válidas dieron el mismo AST en LL y LR.")
    print("-" * 63)

    print("\nCadenas que NO pertenecen a L (ambos deben rechazarlas):")
    for caso in CASOS_INVALIDOS:
        error_ll = error_lr = None
        try:
            parsear_ll(caso)
        except SyntaxError as error:
            error_ll = str(error)
        try:
            parsear_lr(caso, generador_lr)
        except SyntaxError as error:
            error_lr = str(error)
        estado = "AMBOS RECHAZAN" if error_ll and error_lr else "revisar"
        print(f"  '{caso}'  ->  {estado}")
        print(f"      LL: {error_ll}")
        print(f"      LR: {error_lr}")


if __name__ == "__main__":
    ejecutar()
