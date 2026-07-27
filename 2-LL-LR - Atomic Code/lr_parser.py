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
# Analizador sintáctico LR (ascendente, desplazar-reducir) para el MISMO
# lenguaje L que ll_parser.py, pero usando su gramática "natural", recursiva
# por la izquierda, la que un LL(1) no puede procesar:
#
#   E ::= E '+' T | E '-' T | T
#   T ::= T '*' F | T '/' F | F
#   F ::= '(' E ')' | num
#
# En vez de escribir a mano una tabla de estados, este archivo implementa un
# GENERADOR de analizadores SLR(1) genérico (recibe cualquier gramática libre
# de contexto y produce sus tablas), igual a lo que hacen por dentro
# herramientas como Bison o Yacc:
#
#   1) Cierre (closure) y transición (goto) de conjuntos de ítems LR(0).
#   2) Colección canónica de estados (el autómata LR(0)).
#   3) Conjuntos FIRST y FOLLOW de la gramática.
#   4) Tablas ACTION (desplazar / reducir / aceptar) y GOTO, con la regla
#      SLR: se reduce por A -> alfa en el estado i para cada símbolo de
#      FOLLOW(A).
#
# Luego un parser tabla-dirigido (pila de estados + pila de valores) consume
# los tokens y construye el AST al reducir, con la misma traza que produciría
# un parser LR real: en cada paso se ve la pila, la entrada restante y la
# acción tomada (desplazar/reducir/aceptar).
# ---------------------------------------------------------------------------

import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ast_nodes import Nodo, tokenizar, TERMINAL_DE_TOKEN

EPSILON = "EPSILON"
FIN = "$"

# ===========================================================================
#           1) GRAMÁTICA DE L (recursiva por la izquierda, forma "natural")
# ===========================================================================
# Producción 0 = producción aumentada E' -> E, se agrega automáticamente en
# construir_generador(). El resto es la gramática de L tal cual la escribe
# cualquier libro de compiladores para expresiones aritméticas.
SIMBOLO_INICIAL = "E"
PRODUCCIONES_L = [
    ("E", ("E", "+", "T")),
    ("E", ("E", "-", "T")),
    ("E", ("T",)),
    ("T", ("T", "*", "F")),
    ("T", ("T", "/", "F")),
    ("T", ("F",)),
    ("F", ("(", "E", ")")),
    ("F", ("num",)),
]


# ===========================================================================
#           2) FIRST Y FOLLOW (genérico, para cualquier gramática)
# ===========================================================================
def calcular_no_terminales(producciones):
    return {lhs for lhs, _ in producciones}


def primero_de_secuencia(secuencia, first, no_terminales):
    resultado = set()
    for simbolo in secuencia:
        if simbolo not in no_terminales:
            resultado.add(simbolo)
            return resultado
        resultado |= (first[simbolo] - {EPSILON})
        if EPSILON not in first[simbolo]:
            return resultado
    resultado.add(EPSILON)
    return resultado


def calcular_first(producciones, no_terminales):
    first = {nt: set() for nt in no_terminales}
    cambio = True
    while cambio:
        cambio = False
        for lhs, rhs in producciones:
            antes = len(first[lhs])
            first[lhs] |= primero_de_secuencia(rhs, first, no_terminales)
            if len(first[lhs]) != antes:
                cambio = True
    return first


def calcular_follow(producciones, no_terminales, first, simbolo_inicial):
    follow = {nt: set() for nt in no_terminales}
    follow[simbolo_inicial].add(FIN)
    cambio = True
    while cambio:
        cambio = False
        for lhs, rhs in producciones:
            for i, simbolo in enumerate(rhs):
                if simbolo not in no_terminales:
                    continue
                resto = rhs[i + 1:]
                primero_resto = primero_de_secuencia(resto, first, no_terminales)
                antes = len(follow[simbolo])
                follow[simbolo] |= (primero_resto - {EPSILON})
                if EPSILON in primero_resto:
                    follow[simbolo] |= follow[lhs]
                if len(follow[simbolo]) != antes:
                    cambio = True
    return follow


# ===========================================================================
#           3) AUTÓMATA LR(0): CIERRE, GOTO Y COLECCIÓN CANÓNICA
# ===========================================================================
def cerradura(items_iniciales, producciones, no_terminales):
    """Un item es (indice_produccion, posicion_del_punto)."""
    resultado = set(items_iniciales)
    cambio = True
    while cambio:
        cambio = False
        nuevos = set()
        for indice, punto in resultado:
            _, rhs = producciones[indice]
            if punto < len(rhs) and rhs[punto] in no_terminales:
                simbolo = rhs[punto]
                for j, (lhs2, _) in enumerate(producciones):
                    if lhs2 == simbolo and (j, 0) not in resultado:
                        nuevos.add((j, 0))
        if nuevos:
            resultado |= nuevos
            cambio = True
    return frozenset(resultado)


def ir_a(items, simbolo, producciones, no_terminales):
    movidos = {
        (indice, punto + 1)
        for indice, punto in items
        if punto < len(producciones[indice][1]) and producciones[indice][1][punto] == simbolo
    }
    return cerradura(movidos, producciones, no_terminales) if movidos else None


def construir_automata(producciones, no_terminales):
    estado_0 = cerradura({(0, 0)}, producciones, no_terminales)
    estados = [estado_0]
    transiciones = {}
    pendientes = [0]
    while pendientes:
        i = pendientes.pop()
        simbolos_con_punto = {
            producciones[indice][1][punto]
            for indice, punto in estados[i]
            if punto < len(producciones[indice][1])
        }
        for simbolo in sorted(simbolos_con_punto):
            destino = ir_a(estados[i], simbolo, producciones, no_terminales)
            if destino is None:
                continue
            if destino in estados:
                j = estados.index(destino)
            else:
                estados.append(destino)
                j = len(estados) - 1
                pendientes.append(j)
            transiciones[(i, simbolo)] = j
    return estados, transiciones


# ===========================================================================
#           4) TABLAS ACTION / GOTO (algoritmo SLR(1))
# ===========================================================================
def construir_tablas_slr(producciones, no_terminales):
    first = calcular_first(producciones, no_terminales)
    follow = calcular_follow(producciones, no_terminales, first, producciones[0][1][0])
    estados, transiciones = construir_automata(producciones, no_terminales)

    accion = {}
    ir = {}
    for i, items in enumerate(estados):
        for indice, punto in items:
            lhs, rhs = producciones[indice]
            if punto < len(rhs):
                simbolo = rhs[punto]
                if simbolo not in no_terminales:
                    destino = transiciones.get((i, simbolo))
                    if destino is not None:
                        _fijar(accion, (i, simbolo), ("desplazar", destino), i, simbolo)
            else:
                if indice == 0:
                    _fijar(accion, (i, FIN), ("aceptar", None), i, FIN)
                else:
                    for simbolo in follow[lhs]:
                        _fijar(accion, (i, simbolo), ("reducir", indice), i, simbolo)
        for nt in no_terminales:
            destino = transiciones.get((i, nt))
            if destino is not None:
                ir[(i, nt)] = destino
    return estados, accion, ir, first, follow


def _fijar(tabla, clave, valor_nuevo, estado, simbolo):
    if clave in tabla and tabla[clave] != valor_nuevo:
        raise ValueError(
            f"Conflicto SLR en el estado {estado} con el símbolo '{simbolo}': "
            f"{tabla[clave]} vs {valor_nuevo}. La gramática no es SLR(1)."
        )
    tabla[clave] = valor_nuevo


# ===========================================================================
#           5) CONSTRUCCIÓN DEL AST AL REDUCIR CADA PRODUCCIÓN
# ===========================================================================
def construir_nodo_reduccion(lhs, rhs, hijos):
    if lhs in ("E", "T") and len(rhs) == 3 and rhs[1] in ("+", "-", "*", "/"):
        return Nodo("BinOp", [hijos[0], hijos[2]], valor=hijos[1])
    if lhs == "F" and len(rhs) == 3 and rhs[0] == "(":
        return hijos[1]
    # producciones "de paso" (E->T, T->F): el hijo ya es el nodo correcto
    return hijos[0]


# ===========================================================================
#           6) PARSER TABLA-DIRIGIDO (desplazar / reducir / aceptar)
# ===========================================================================
class GeneradorLR:
    def __init__(self, producciones_base, simbolo_inicial):
        aumentado = simbolo_inicial + "'"
        self.producciones = [(aumentado, (simbolo_inicial,))] + list(producciones_base)
        self.no_terminales = calcular_no_terminales(self.producciones)
        (self.estados, self.accion, self.ir,
         self.first, self.follow) = construir_tablas_slr(self.producciones, self.no_terminales)

    def analizar(self, tokens):
        pila_estados = [0]
        pila_valores = []
        traza = []
        i = 0
        while True:
            estado = pila_estados[-1]
            tipo_tok, val_tok = tokens[i]
            simbolo = TERMINAL_DE_TOKEN[tipo_tok]
            clave = (estado, simbolo)
            resumen_pila = "[" + " ".join(str(e) for e in pila_estados) + "]"
            resumen_entrada = " ".join(TERMINAL_DE_TOKEN[t] for t, _ in tokens[i:])
            if clave not in self.accion:
                raise SyntaxError(
                    f"LR: error de sintaxis en el token {tokens[i]} (estado {estado}); "
                    f"pila={resumen_pila} entrada={resumen_entrada}"
                )
            movimiento, destino = self.accion[clave]
            if movimiento == "desplazar":
                traza.append(f"pila={resumen_pila:<18} entrada={resumen_entrada:<20} accion=desplazar -> estado {destino}")
                pila_estados.append(destino)
                pila_valores.append(Nodo("Num", valor=val_tok) if tipo_tok == "NUM" else val_tok)
                i += 1
            elif movimiento == "reducir":
                lhs, rhs = self.producciones[destino]
                traza.append(f"pila={resumen_pila:<18} entrada={resumen_entrada:<20} accion=reducir {lhs} -> {' '.join(rhs)}")
                hijos = []
                for _ in rhs:
                    pila_estados.pop()
                    hijos.insert(0, pila_valores.pop())
                nodo = construir_nodo_reduccion(lhs, rhs, hijos)
                cima = pila_estados[-1]
                pila_estados.append(self.ir[(cima, lhs)])
                pila_valores.append(nodo)
            elif movimiento == "aceptar":
                traza.append(f"pila={resumen_pila:<18} entrada={resumen_entrada:<20} accion=ACEPTAR")
                return pila_valores[-1], traza
            else:
                raise SyntaxError("LR: movimiento desconocido en la tabla ACTION")


def parsear_lr(texto, generador=None):
    generador = generador or GeneradorLR(PRODUCCIONES_L, SIMBOLO_INICIAL)
    tokens = tokenizar(texto)
    ast, traza = generador.analizar(tokens)
    return ast, traza, generador


if __name__ == "__main__":
    from ast_nodes import imprimir_arbol

    generador = GeneradorLR(PRODUCCIONES_L, SIMBOLO_INICIAL)
    print(f"Autómata LR(0): {len(generador.estados)} estados construidos por cierre/goto.\n")

    entrada = "(3 + 4) * 2 - 1"
    ast, traza, _ = parsear_lr(entrada, generador)
    print(f"Entrada: {entrada}\n")
    print("Traza de análisis (LR, desplazar-reducir):")
    for paso in traza:
        print("  " + paso)
    print("\nAST:")
    imprimir_arbol(ast)
