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
# Lexer + parser para extraer las interfaces de red de un archivo Docker
# Compose. NO es un parser YAML general: reconoce el subconjunto necesario
# para esta tarea (bloques 'services:' y 'networks:', con indentación
# uniforme de 2 espacios por nivel, que es como se generan las muestras de
# 'generar_muestras.py'). Esta misma versión (algoritmo y formato de salida)
# se reimplementa en C y Rust para el experimento de tiempos de ejecución,
# de modo que la comparación entre lenguajes sea justa.
#
# Léxico (por línea): se ignoran líneas en blanco y comentarios ('#'). Cada
# línea se clasifica en: indentación (espacios al inicio), si es ITEM de
# lista ('- '), y CLAVE: VALOR (o solo VALOR si es un escalar suelto de una
# lista, ej. '- frontend').
#
# Sintáctico: se mantiene una pila de (indentación, clave) que reconstruye la
# RUTA de claves ancestras de cada línea (como en un YAML real). Contra esa
# ruta se contrastan patrones fijos, ej. ["networks", <red>, "driver"], que
# es la "gramática" de lo que sabemos interpretar; toda ruta que no matchea
# ninguno de esos patrones (version, volumes, image, etc.) simplemente se
# ignora.
#
# Uso:      python compose_netparser.py archivo.yml
# Salida:   bloque REDES (una por línea) y bloque INTERFACES (una fila por
#           cada red a la que se conecta cada servicio), en un formato de
#           texto plano fijo e idéntico entre las 3 implementaciones.
# ---------------------------------------------------------------------------

import sys


def analizar_linea(linea_cruda):
    """Léxico de una línea: (indentacion_efectiva, clave_o_None, valor)."""
    sin_salto = linea_cruda.rstrip("\n").rstrip("\r")
    indent = len(sin_salto) - len(sin_salto.lstrip(" "))
    contenido = sin_salto.strip()
    if contenido == "" or contenido.startswith("#"):
        return None

    if contenido.startswith("- "):
        contenido = contenido[2:]
        indent += 2
    elif contenido == "-":
        return None

    if ":" in contenido:
        clave, _, valor = contenido.partition(":")
        clave = clave.strip()
        valor = valor.strip()
        if valor == "":
            valor = None
        return (indent, clave, valor)
    return (indent, None, contenido.strip())


def analizar_compose(lineas):
    """Recorre el archivo y devuelve (redes, interfaces).
    redes:      lista de dicts {nombre, driver, subnet, gateway}
    interfaces: lista de dicts {servicio, red, ip}
    """
    redes = []
    redes_por_nombre = {}
    interfaces = []

    pila = [(-1, None)]  # (indentacion, clave) ; raiz virtual

    for linea_cruda in lineas:
        analizado = analizar_linea(linea_cruda)
        if analizado is None:
            continue
        indent, clave, valor = analizado

        while pila[-1][0] >= indent:
            pila.pop()

        ruta = [k for _, k in pila[1:]]
        if clave is not None:
            ruta_completa = ruta + [clave]
        else:
            ruta_completa = ruta + ["*"]

        # --- reglas de la gramática que reconocemos ------------------------
        if ruta_completa == ["networks", clave] and clave is not None and len(ruta) == 1:
            redes_por_nombre[clave] = {"nombre": clave, "driver": "bridge", "subnet": None, "gateway": None}
            redes.append(redes_por_nombre[clave])
        elif len(ruta_completa) == 3 and ruta_completa[0] == "networks" and ruta_completa[2] == "driver":
            nombre_red = ruta_completa[1]
            if nombre_red in redes_por_nombre:
                redes_por_nombre[nombre_red]["driver"] = valor
        elif len(ruta_completa) == 5 and ruta_completa[0] == "networks" and ruta_completa[2] == "ipam" \
                and ruta_completa[3] == "config" and ruta_completa[4] in ("subnet", "gateway"):
            nombre_red = ruta_completa[1]
            if nombre_red in redes_por_nombre:
                redes_por_nombre[nombre_red][ruta_completa[4]] = valor
        elif len(ruta_completa) == 4 and ruta_completa[0] == "services" and ruta_completa[2] == "networks" \
                and ruta_completa[3] == "*":
            servicio = ruta_completa[1]
            interfaces.append({"servicio": servicio, "red": valor, "ip": None})
        elif len(ruta_completa) == 4 and ruta_completa[0] == "services" and ruta_completa[2] == "networks":
            servicio = ruta_completa[1]
            nombre_red = ruta_completa[3]
            interfaces.append({"servicio": servicio, "red": nombre_red, "ip": None})
        elif len(ruta_completa) == 5 and ruta_completa[0] == "services" and ruta_completa[2] == "networks" \
                and ruta_completa[4] == "ipv4_address":
            servicio = ruta_completa[1]
            nombre_red = ruta_completa[3]
            for interfaz in reversed(interfaces):
                if interfaz["servicio"] == servicio and interfaz["red"] == nombre_red:
                    interfaz["ip"] = valor
                    break

        if clave is not None:
            pila.append((indent, clave))

    return redes, interfaces


def formatear_salida(redes, interfaces):
    lineas = ["REDES:"]
    for red in redes:
        lineas.append(
            f"nombre={red['nombre']} driver={red['driver'] or '-'} "
            f"subnet={red['subnet'] or '-'} gateway={red['gateway'] or '-'}"
        )
    lineas.append("")
    lineas.append("INTERFACES:")
    for interfaz in interfaces:
        lineas.append(
            f"servicio={interfaz['servicio']} red={interfaz['red']} ip={interfaz['ip'] or '-'}"
        )
    return "\n".join(lineas)


def main():
    if len(sys.argv) != 2:
        print("Uso: python compose_netparser.py <archivo docker-compose.yml>", file=sys.stderr)
        sys.exit(1)
    with open(sys.argv[1], "r", encoding="utf-8") as archivo:
        lineas = archivo.readlines()
    redes, interfaces = analizar_compose(lineas)
    print(formatear_salida(redes, interfaces))


if __name__ == "__main__":
    main()
