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
# Motor de sugerencias que representa, para UnegScript, el "fallback a IA"
# descrito en la sección 6 del enunciado del Tema 5: cuando el lexer o el
# parser tradicionales no reconocen algo, en vez de simplemente fallar se
# calcula qué tan "seguro" está el sistema de una corrección (umbral de
# confianza) y, si hace falta, se consulta una capa adicional de sugerencias.
#
# Esta máquina no tiene una API key de IA configurada, así que la "consulta a
# un LLM" del punto 6.1 del PDF se SIMULA localmente en
# consultar_ia_simulada(): en vez de una llamada de red, usa un corpus propio
# de errores comunes de UnegScript. La función queda deliberadamente aislada
# del resto (lexer/parser no conocen su implementación interna, solo llaman
# a evaluar_token_desconocido / sugerir_reparacion_sintactica) para que, el
# día que el equipo quiera conectar una API real, solo haya que reemplazar
# el cuerpo de esa función.
#
# El cálculo de confianza es exactamente el de la sección 6.2 del PDF:
#   ratio = SequenceMatcher(None, lexema, candidato).ratio()
# que para ("pront", "print") da 0.8 y para ("prnt", "print") da ~0.89,
# los mismos números que trae el enunciado.
# ---------------------------------------------------------------------------

from collections import namedtuple
from difflib import SequenceMatcher

UMBRAL_ALTO = 0.8   # confianza suficiente para autocorregir directo
UMBRAL_BAJO = 0.5   # por debajo de esto, ni la IA simulada arriesga una sugerencia

# Vocabulario conocido de UnegScript contra el que se mide la confianza.
PALABRAS_CLAVE = {"if": "KW_IF", "else": "KW_ELSE", "print": "KW_PRINT"}

# Corpus propio de errores comunes (lo que en un LLM real vendría de su
# entrenamiento); el motor simulado lo consulta cuando la heurística local
# por sí sola no alcanza el umbral alto.
CORPUS_ERRORES_COMUNES = {
    "fi": "if", "esle": "else", "els": "else", "eles": "else",
    "pritn": "print", "prin": "print", "prit": "print", "printt": "print",
}

Sugerencia = namedtuple("Sugerencia", ["original", "corregido", "confianza", "fuente", "contexto"])


def calcular_confianza(lexema, candidato):
    """ratio = 1 - distancia_edicion / max(len) ; sección 6.2 del PDF."""
    return SequenceMatcher(None, lexema, candidato).ratio()


def _mejor_candidato(lexema, vocabulario):
    mejor, mejor_ratio = None, 0.0
    for candidato in vocabulario:
        ratio = calcular_confianza(lexema, candidato)
        if ratio > mejor_ratio:
            mejor, mejor_ratio = candidato, ratio
    return mejor, mejor_ratio


def consultar_ia_simulada(lexema, vocabulario, contexto=""):
    """Representa la consulta a un LLM ('Corrige este token ambiguo en
    contexto de UnegScript: <lexema>', sección 6.1). Simulada localmente."""
    if lexema in CORPUS_ERRORES_COMUNES:
        return Sugerencia(lexema, CORPUS_ERRORES_COMUNES[lexema], 0.99, "motor de IA simulado", contexto)
    candidato, ratio = _mejor_candidato(lexema, vocabulario)
    if candidato is not None and ratio >= UMBRAL_BAJO:
        return Sugerencia(lexema, candidato, ratio, "motor de IA simulado", contexto)
    return None


def evaluar_token_desconocido(lexema, vocabulario=None, contexto=""):
    """Punto de entrada del lexer híbrido para un lexema que no matcheó
    ninguna palabra clave. Devuelve una Sugerencia o None si el lexema
    parece un identificador legítimo (confianza demasiado baja para ser
    un typo de algo conocido)."""
    vocabulario = vocabulario or list(PALABRAS_CLAVE)
    candidato, ratio = _mejor_candidato(lexema, vocabulario)
    if candidato is None:
        return None
    if ratio >= UMBRAL_ALTO:
        return Sugerencia(lexema, candidato, ratio, "heurística local (difflib)", contexto)
    if ratio >= UMBRAL_BAJO:
        return consultar_ia_simulada(lexema, vocabulario, contexto)
    return None


def sugerir_reparacion_sintactica(tipo_esperado, token_encontrado, contexto=""):
    """Punto de entrada del parser cuando el lookahead no matchea la
    producción esperada. No hay corpus de gramáticas rotas contra qué medir
    una 'confianza' numérica, así que el motor simulado devuelve un mensaje
    de reparación en lenguaje natural, como haría un LLM real consultado con
    un prompt de la forma 'falta <tipo_esperado> cerca de <token>'."""
    tipo_encontrado, lexema_encontrado = token_encontrado
    mensaje = f"falta {tipo_esperado} {contexto}".strip() + f" (se encontró {tipo_encontrado} {lexema_encontrado!r})"
    return Sugerencia(lexema_encontrado, tipo_esperado, None, "motor de IA simulado", mensaje)
