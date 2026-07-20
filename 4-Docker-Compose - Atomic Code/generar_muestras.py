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
# Genera las n muestras de archivos docker-compose.yml usadas por el
# experimento de tiempos (ejecutar_experimento.py). El enunciado pide
# 5 < n < 20 archivos; aquí se generan n=12, con cantidad de servicios
# creciente (de 1 a 40) para que el experimento también muestre cómo escala
# cada implementación con el tamaño del archivo.
#
# Cada archivo generado respeta el subconjunto de Docker Compose que
# reconoce compose_netparser (indentación uniforme de 2 espacios, bloque
# 'services' con 'networks' en forma de lista o de mapeo con
# 'ipv4_address', y bloque 'networks' con 'driver' e 'ipam.config'). Es
# determinístico: no usa aleatoriedad, para que el experimento sea
# reproducible.
#
# Uso: python generar_muestras.py
# ---------------------------------------------------------------------------

import os

from directorio_base import directorio_base

CANTIDAD_SERVICIOS = [1, 2, 3, 5, 8, 12, 16, 20, 25, 30, 35, 40]


def generar_compose(n_servicios):
    n_redes = max(1, -(-n_servicios // 6))  # techo(n_servicios / 6), minimo 1
    redes = [f"red{r}" for r in range(n_redes)]

    lineas = ['version: "3.8"', "services:"]
    for i in range(n_servicios):
        servicio = f"servicio{i:03d}"
        cuantas_redes = 1 + (i % 3)  # 1, 2 o 3 redes por servicio
        redes_asignadas = [redes[(i + k) % n_redes] for k in range(cuantas_redes)]

        lineas.append(f"  {servicio}:")
        lineas.append(f"    image: atomic/demo:{i}")
        lineas.append("    networks:")

        usa_mapeo = (i % 4 == 3)  # 1 de cada 4 servicios usa la forma mapeo (con IP estatica)
        if usa_mapeo:
            for j, red in enumerate(redes_asignadas):
                lineas.append(f"      {red}:")
                if j == 0:
                    octeto = (i % 250) + 2
                    lineas.append(f"        ipv4_address: 10.{n_redes % 200}.{i % 200}.{octeto}")
        else:
            for red in redes_asignadas:
                lineas.append(f"      - {red}")

    lineas.append("")
    lineas.append("networks:")
    for idx, red in enumerate(redes):
        lineas.append(f"  {red}:")
        lineas.append("    driver: bridge")
        lineas.append("    ipam:")
        lineas.append("      config:")
        lineas.append(f"        - subnet: 10.{idx}.0.0/16")
        lineas.append(f"          gateway: 10.{idx}.0.1")
    lineas.append("")
    return "\n".join(lineas)


def main():
    base = os.path.join(directorio_base(), "muestras")
    os.makedirs(base, exist_ok=True)
    generados = []
    for n in CANTIDAD_SERVICIOS:
        contenido = generar_compose(n)
        nombre = f"compose_{n:03d}_servicios.yml"
        ruta = os.path.join(base, nombre)
        with open(ruta, "w", encoding="utf-8", newline="\n") as archivo:
            archivo.write(contenido)
        generados.append((nombre, n, contenido.count("\n") + 1))

    print(f"Generadas {len(generados)} muestras en '{base}':")
    for nombre, n_servicios, n_lineas in generados:
        print(f"  {nombre:32s} servicios={n_servicios:<4} lineas={n_lineas}")


if __name__ == "__main__":
    main()
