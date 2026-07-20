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
# Punto de entrada único de la Pregunta 4 (Docker Compose): corre en
# secuencia los tres pasos que hasta ahora había que ejecutar por separado:
#
#   1) generar_muestras.py     -> crea las 12 muestras docker-compose.yml
#   2) ejecutar_experimento.py -> compila C (gcc) y Rust (cargo), verifica
#                                  que las 3 implementaciones coincidan y
#                                  mide los tiempos -> resultados.csv
#   3) graficar_resultados.py  -> resultados.csv -> resultados_tiempos.png
#
# Este mismo archivo es el que se empaqueta con PyInstaller para producir
# ejecutar_todo.exe (ver README.md, sección "Generar el .exe"). El .exe debe
# quedar en esta misma carpeta ("4-Docker-Compose - Atomic Code"), junto a
# c/, rust/, python/ y muestras/, porque sigue necesitando gcc y cargo
# instalados en la máquina donde se ejecute para compilar C y Rust.
#
# Uso: python ejecutar_todo.py        (o doble clic en ejecutar_todo.exe)
# ---------------------------------------------------------------------------

import shutil
import sys

import generar_muestras
import ejecutar_experimento
import graficar_resultados
from directorio_base import directorio_base


def verificar_herramientas():
    requeridas = ["gcc", "cargo"]
    if getattr(sys, "frozen", False):
        # corriendo como ejecutar_todo.exe: sys.executable es el propio
        # .exe, así que además hace falta un Python real en el PATH para
        # medir la implementación en Python (ver _resolver_interprete_python
        # en ejecutar_experimento.py).
        requeridas.append("python")
    faltantes = [nombre for nombre in requeridas if shutil.which(nombre) is None]
    if faltantes:
        print("No se encontraron en el PATH: " + ", ".join(faltantes))
        print("Se necesitan gcc (para compilar C), cargo (para compilar Rust)"
              + (" y python (para correr la implementación en Python)." if "python" in faltantes else "."))
        return False
    return True


def main():
    print("=" * 63)
    print(" Pregunta 4 - Docker Compose: lexer/parser en C, Rust y Python")
    print("                    Equipo: Atomic Code")
    print("=" * 63)
    print(f"\nCarpeta de trabajo: {directorio_base()}\n")

    if not verificar_herramientas():
        return 1

    print("-" * 63)
    print(" Paso 1/3: generando las muestras docker-compose.yml")
    print("-" * 63)
    generar_muestras.main()

    print("\n" + "-" * 63)
    print(" Paso 2/3: compilando, verificando y midiendo tiempos")
    print("-" * 63)
    ejecutar_experimento.main()

    print("\n" + "-" * 63)
    print(" Paso 3/3: generando la gráfica de resultados")
    print("-" * 63)
    graficar_resultados.main()

    print("\n" + "=" * 63)
    print(" Listo. Revisa 'resultados.csv' y 'resultados_tiempos.png'")
    print(f" en: {directorio_base()}")
    print("=" * 63)
    return 0


if __name__ == "__main__":
    codigo_salida = 1
    try:
        codigo_salida = main()
    except Exception as error:
        print(f"\nOcurrió un error y el proceso se detuvo: {error}")
        codigo_salida = 1
    finally:
        # Mantiene la ventana abierta cuando se hace doble clic en el .exe;
        # si no hay una consola real detrás (stdin redirigido o cerrado,
        # como al correr el .exe desde un script), simplemente se omite.
        try:
            input("\nPresione ENTER para salir...")
        except (EOFError, OSError):
            pass
    sys.exit(codigo_salida)
