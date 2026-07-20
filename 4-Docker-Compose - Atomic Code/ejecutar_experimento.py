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
# Experimento de carga: compila las 3 implementaciones del lexer/parser de
# Docker Compose (C, Rust, Python) y las ejecuta contra cada una de las n
# muestras generadas por generar_muestras.py, midiendo el tiempo de
# ejecución de cada invocación (proceso completo, de punta a punta) con
# time.perf_counter(). Cada combinación (implementación, archivo) se corre
# REPETICIONES veces para reducir el ruido de la medición.
#
# Antes de medir, se verifica que las 3 implementaciones extraigan EXACTAMENTE
# lo mismo (mismas redes e interfaces) para cada muestra; si alguna difiere,
# el experimento se detiene, porque una comparación de tiempos solo es válida
# si los programas hacen el mismo trabajo.
#
# Salida: resultados.csv (una fila por repetición) para que
# graficar_resultados.py genere las gráficas de tiempo de ejecución.
#
# Uso: python ejecutar_experimento.py
# ---------------------------------------------------------------------------

import csv
import os
import re
import shutil
import subprocess
import sys
import time

from directorio_base import directorio_base

BASE = directorio_base()
DIR_MUESTRAS = os.path.join(BASE, "muestras")
DIR_C = os.path.join(BASE, "c")
DIR_RUST = os.path.join(BASE, "rust")
DIR_PYTHON = os.path.join(BASE, "python")

EXE_C = os.path.join(DIR_C, "compose_netparser.exe")
EXE_RUST = os.path.join(DIR_RUST, "target", "release", "compose_netparser.exe")
SCRIPT_PYTHON = os.path.join(DIR_PYTHON, "compose_netparser.py")

REPETICIONES = 7


def _resolver_interprete_python():
    """sys.executable solo sirve tal cual cuando este script corre con un
    Python normal. Si ejecutar_todo.py fue empaquetado con PyInstaller
    (ejecutar_todo.exe), sys.executable apunta al PROPIO .exe, no a un
    intérprete de Python; usarlo tal cual haría que cada medición de la
    implementación 'Python' relance recursivamente el .exe completo en vez
    de correr compose_netparser.py. En ese caso se busca un 'python' real
    en el PATH del sistema (necesario de todas formas para comparar contra
    un Python real, no contra el propio empaquetado)."""
    if not getattr(sys, "frozen", False):
        return sys.executable
    encontrado = shutil.which("python") or shutil.which("python3")
    if encontrado is None:
        raise RuntimeError(
            "No se encontró un intérprete de Python en el PATH del sistema; "
            "se necesita uno real para medir la implementación en Python."
        )
    return encontrado


PYTHON_REAL = _resolver_interprete_python()


def compilar_todo():
    print("Compilando implementación C (gcc)...")
    # -o se pasa con el nombre relativo (no la ruta completa de EXE_C): el
    # linker de MinGW (ld.exe) puede fallar con "Illegal byte sequence" si la
    # ruta del proyecto tiene tildes/ñ y la consola no está en codepage UTF-8
    # (pasa en PowerShell con la codepage por defecto). Como cwd=DIR_C, con
    # el nombre relativo alcanza y se evita pasarle esa ruta como argumento.
    subprocess.run(
        ["gcc", "-O2", "-o", os.path.basename(EXE_C), "compose_netparser.c"],
        cwd=DIR_C, check=True,
    )
    print("Compilando implementación Rust (cargo build --release)...")
    subprocess.run(
        ["cargo", "build", "--release", "--quiet"],
        cwd=DIR_RUST, check=True,
    )
    print("Listo.\n")


def comando_para(implementacion, archivo):
    # se pasa solo el nombre del archivo (sin la ruta), y se corre con
    # cwd=DIR_MUESTRAS: así el nombre de la carpeta del proyecto (que puede
    # tener tildes, como en este caso "Programación") nunca llega como
    # argumento de línea de comandos al programa compilado en C, que sí
    # puede tener problemas leyendo argv con acentos según la codepage de
    # la consola activa.
    nombre = os.path.basename(archivo)
    if implementacion == "C":
        return [EXE_C, nombre]
    if implementacion == "Rust":
        return [EXE_RUST, nombre]
    if implementacion == "Python":
        return [PYTHON_REAL, SCRIPT_PYTHON, nombre]
    raise ValueError(implementacion)


def salida_normalizada(implementacion, archivo):
    resultado = subprocess.run(
        comando_para(implementacion, archivo),
        cwd=DIR_MUESTRAS, capture_output=True, text=True, check=True,
    )
    return resultado.stdout.replace("\r\n", "\n").strip()


def verificar_consistencia(archivos):
    print("Verificando que C, Rust y Python extraigan lo mismo en cada muestra...")
    for archivo in archivos:
        referencia = salida_normalizada("Python", archivo)
        for implementacion in ("C", "Rust"):
            salida = salida_normalizada(implementacion, archivo)
            if salida != referencia:
                print(f"\n¡Diferencia encontrada! {implementacion} vs Python en {os.path.basename(archivo)}")
                print("--- Python ---")
                print(referencia)
                print(f"--- {implementacion} ---")
                print(salida)
                raise SystemExit(1)
    print("Las 3 implementaciones coinciden en todas las muestras.\n")


def medir_tiempo(implementacion, archivo):
    comando = comando_para(implementacion, archivo)
    inicio = time.perf_counter()
    subprocess.run(comando, cwd=DIR_MUESTRAS, capture_output=True, check=True)
    return time.perf_counter() - inicio


def listar_muestras():
    archivos = sorted(
        os.path.join(DIR_MUESTRAS, nombre)
        for nombre in os.listdir(DIR_MUESTRAS)
        if nombre.endswith(".yml")
    )
    return archivos


def metadatos_de(archivo):
    nombre = os.path.basename(archivo)
    coincidencia = re.search(r"(\d+)_servicios", nombre)
    servicios = int(coincidencia.group(1)) if coincidencia else 0
    with open(archivo, "r", encoding="utf-8") as f:
        lineas = sum(1 for _ in f)
    return nombre, servicios, lineas


def main():
    compilar_todo()
    archivos = listar_muestras()
    if not archivos:
        print("No hay muestras en 'muestras/'. Ejecuta primero generar_muestras.py.")
        raise SystemExit(1)

    verificar_consistencia(archivos)

    filas = []
    implementaciones = ["C", "Rust", "Python"]
    print(f"Midiendo {len(implementaciones)} implementaciones x {len(archivos)} archivos "
          f"x {REPETICIONES} repeticiones...\n")

    for archivo in archivos:
        nombre, servicios, lineas = metadatos_de(archivo)
        print(f"  {nombre} (servicios={servicios}, lineas={lineas})")
        for implementacion in implementaciones:
            medir_tiempo(implementacion, archivo)  # corrida de calentamiento, se descarta
            for repeticion in range(1, REPETICIONES + 1):
                tiempo = medir_tiempo(implementacion, archivo)
                filas.append({
                    "implementacion": implementacion,
                    "archivo": nombre,
                    "servicios": servicios,
                    "lineas": lineas,
                    "repeticion": repeticion,
                    "tiempo_segundos": f"{tiempo:.6f}",
                })
            tiempos = [float(f["tiempo_segundos"]) for f in filas
                       if f["archivo"] == nombre and f["implementacion"] == implementacion]
            print(f"    {implementacion:8s} promedio={sum(tiempos)/len(tiempos)*1000:.3f} ms")

    ruta_csv = os.path.join(BASE, "resultados.csv")
    with open(ruta_csv, "w", newline="", encoding="utf-8") as archivo_csv:
        escritor = csv.DictWriter(archivo_csv, fieldnames=[
            "implementacion", "archivo", "servicios", "lineas", "repeticion", "tiempo_segundos",
        ])
        escritor.writeheader()
        escritor.writerows(filas)

    print(f"\nResultados guardados en {ruta_csv} ({len(filas)} filas).")


if __name__ == "__main__":
    main()
