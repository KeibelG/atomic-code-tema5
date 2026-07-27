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
# Lexer híbrido de UnegScript: primero corre el analizador léxico
# tradicional (patrones regex, equivalente a un autómata finito) sobre el
# código fuente. Toda palabra que no coincide con una palabra clave conocida
# ("if", "else", "print") se manda a motor_ia_simulado.evaluar_token_desconocido,
# que calcula la confianza de similitud contra el vocabulario; si supera el
# umbral (>= 0.8 directo, o >= 0.5 vía el "motor de IA") el token se corrige
# automáticamente y se registra la sugerencia. Si la confianza es demasiado
# baja, el lexema se deja como identificador normal (ID): no todo lo que no
# es palabra clave es un error, la mayoría son variables legítimas.
#
# Gramática léxica de UnegScript (subconjunto de Python usado en el tema):
#   NUM      ::= [0-9]+
#   STRING   ::= '"' ... '"'
#   ID       ::= [A-Za-z_][A-Za-z0-9_]*   (incluye palabras clave y typos)
#   operadores: = == != >= <= > < + - * / ( ) ;
# ---------------------------------------------------------------------------

import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import motor_ia_simulado as ia

ESPECIFICACION_TOKENS = [
    ("NUM", r"\d+"),
    ("STRING", r'"[^"]*"'),
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
    ("PUNTOYCOMA", r";"),
    ("PALABRA", r"[A-Za-z_][A-Za-z0-9_]*"),
    ("ESPACIO", r"\s+"),
]
REGEX_TOKENS = "|".join(f"(?P<{nombre}>{patron})" for nombre, patron in ESPECIFICACION_TOKENS)


def _tokenizar_bruto(texto):
    tokens = []
    pos = 0
    for coincidencia in re.finditer(REGEX_TOKENS, texto):
        if coincidencia.start() != pos:
            fragmento = texto[pos:coincidencia.start()]
            raise SyntaxError(f"carácter no reconocido cerca de {fragmento!r}")
        tipo = coincidencia.lastgroup
        valor = coincidencia.group(tipo)
        pos = coincidencia.end()
        if tipo != "ESPACIO":
            tokens.append((tipo, valor))
    if pos != len(texto):
        raise SyntaxError(f"carácter no reconocido cerca de {texto[pos:]!r}")
    return tokens


def lexer_hibrido(texto):
    """Devuelve (tokens_corregidos, sugerencias). tokens_corregidos incluye
    el marcador de fin ('FIN', '$')."""
    tokens_finales = []
    sugerencias = []

    for tipo, valor in _tokenizar_bruto(texto):
        if tipo == "PALABRA" and valor not in ia.PALABRAS_CLAVE:
            sugerencia = ia.evaluar_token_desconocido(valor, contexto=f"token '{valor}'")
            if sugerencia is not None:
                sugerencias.append(sugerencia)
                tokens_finales.append((ia.PALABRAS_CLAVE[sugerencia.corregido], sugerencia.corregido))
            else:
                tokens_finales.append(("ID", valor))
        elif tipo == "PALABRA":
            tokens_finales.append((ia.PALABRAS_CLAVE[valor], valor))
        else:
            tokens_finales.append((tipo, valor))

    tokens_finales.append(("FIN", "$"))
    return tokens_finales, sugerencias


if __name__ == "__main__":
    fuente = 'pront x=5; if x>3 prnt(x) else prnt("no")'
    tokens, sugerencias = lexer_hibrido(fuente)
    print(f"Entrada: {fuente}\n")
    print("Tokens corregidos:")
    for tok in tokens:
        print(f"  {tok}")
    print("\nSugerencias IA:")
    for s in sugerencias:
        print(f"  Sugerencia: '{s.original}' -> '{s.corregido}'  (confianza={s.confianza:.2f}, fuente={s.fuente})")
