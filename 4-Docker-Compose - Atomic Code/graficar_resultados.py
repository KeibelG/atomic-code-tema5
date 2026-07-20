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
# Lee resultados.csv (generado por ejecutar_experimento.py) y produce
# resultados_tiempos.png con dos gráficas: 1) tiempo promedio de ejecución
# por cantidad de servicios del archivo, una línea por implementación
# (C, Rust, Python); 2) barras del tiempo promedio total por implementación.
#
# Uso: python graficar_resultados.py
# ---------------------------------------------------------------------------

import csv
import os
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from directorio_base import directorio_base

BASE = directorio_base()
RUTA_CSV = os.path.join(BASE, "resultados.csv")
RUTA_PNG = os.path.join(BASE, "resultados_tiempos.png")

COLORES = {"C": "#1f77b4", "Rust": "#d62728", "Python": "#2ca02c"}


def leer_resultados():
    filas = []
    with open(RUTA_CSV, "r", encoding="utf-8") as archivo:
        for fila in csv.DictReader(archivo):
            fila["servicios"] = int(fila["servicios"])
            fila["tiempo_segundos"] = float(fila["tiempo_segundos"])
            filas.append(fila)
    return filas


def promedio_por_servicios(filas):
    """implementacion -> lista ordenada de (servicios, tiempo_promedio_ms)"""
    acumulado = defaultdict(lambda: defaultdict(list))
    for fila in filas:
        acumulado[fila["implementacion"]][fila["servicios"]].append(fila["tiempo_segundos"] * 1000)

    resultado = {}
    for implementacion, por_servicios in acumulado.items():
        puntos = sorted(
            (servicios, sum(tiempos) / len(tiempos))
            for servicios, tiempos in por_servicios.items()
        )
        resultado[implementacion] = puntos
    return resultado


def graficar(filas):
    puntos = promedio_por_servicios(filas)
    implementaciones = sorted(puntos.keys(), key=lambda nombre: sum(t for _, t in puntos[nombre]))

    fig, (ax_lineas, ax_barras) = plt.subplots(1, 2, figsize=(13, 5))

    for implementacion in implementaciones:
        xs = [s for s, _ in puntos[implementacion]]
        ys = [t for _, t in puntos[implementacion]]
        ax_lineas.plot(xs, ys, marker="o", label=implementacion,
                        color=COLORES.get(implementacion))
    ax_lineas.set_xlabel("Cantidad de servicios en el archivo docker-compose")
    ax_lineas.set_ylabel("Tiempo de ejecución promedio (ms)")
    ax_lineas.set_title("Tiempo de ejecución vs tamaño del archivo")
    ax_lineas.legend()
    ax_lineas.grid(True, alpha=0.3)

    promedios_totales = {
        implementacion: sum(t for _, t in puntos[implementacion]) / len(puntos[implementacion])
        for implementacion in implementaciones
    }
    ax_barras.bar(
        promedios_totales.keys(), promedios_totales.values(),
        color=[COLORES.get(nombre) for nombre in promedios_totales],
    )
    ax_barras.set_ylabel("Tiempo de ejecución promedio (ms)")
    ax_barras.set_title("Promedio general por implementación (todas las muestras)")
    for i, (nombre, valor) in enumerate(promedios_totales.items()):
        ax_barras.text(i, valor, f"{valor:.2f} ms", ha="center", va="bottom")

    fig.suptitle("Experimento de tiempos: lexer/parser de interfaces de red de Docker Compose\nEquipo Atomic Code")
    fig.tight_layout()
    fig.savefig(RUTA_PNG, dpi=150)
    print(f"Gráfica guardada en {RUTA_PNG}")


def main():
    if not os.path.exists(RUTA_CSV):
        print("No existe resultados.csv. Ejecuta primero ejecutar_experimento.py.")
        raise SystemExit(1)
    filas = leer_resultados()
    graficar(filas)


if __name__ == "__main__":
    main()
