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
# Ubica la carpeta "4-Docker-Compose - Atomic Code" tanto si los scripts se
# corren directo con "python archivo.py" como si se corren empaquetados
# dentro de ejecutar_todo.exe (generado con PyInstaller). En modo empaquetado
# (--onefile), sys.__file__ apunta a una carpeta temporal que se borra al
# cerrar el programa, así que en ese caso se usa la carpeta donde está el
# propio .exe para que muestras/, resultados.csv y resultados_tiempos.png
# queden junto a él y no se pierdan.
# ---------------------------------------------------------------------------

import os
import sys


def directorio_base():
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))
