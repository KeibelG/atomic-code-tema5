/*
 * Lenguaje:   C (C11)
 * Asignatura: Lenguajes y compiladores
 * Equipo:     Atomic Code
 *             Segmentando el codigo, construyendo la logica
 *
 * Integrantes:
 *   - Victor Vargas    C.I: 30.697.219
 *   - Keibel Guilarte  C.I: 28.726.605
 *   - Oriana Marquez   C.I: 31.354.299
 *   - Jeanny Monagas   C.I: 30.857.471
 *
 * ---------------------------------------------------------------------------
 *                           DESCRIPCION
 * ---------------------------------------------------------------------------
 * Version en C del lexer + parser de interfaces de red de Docker Compose.
 * Mismo algoritmo y mismo formato de salida que python/compose_netparser.py
 * y rust/src/main.rs, para que el experimento de tiempos compare directamente
 * la implementacion del mismo analisis en tres lenguajes distintos.
 *
 * Lexico por linea: se ignoran lineas en blanco y comentarios ('#'). Cada
 * linea se clasifica en indentacion efectiva, clave y valor (o solo valor si
 * es un escalar suelto de una lista, ej. '- frontend').
 *
 * Sintactico: se mantiene una pila de (indentacion, clave) que reconstruye la
 * ruta de claves ancestras de cada linea, igual que en la version Python;
 * contra esa ruta se contrastan los mismos patrones fijos de
 * 'services.<svc>.networks' y 'networks.<red>...'.
 *
 * Uso:      compose_netparser.exe archivo.yml
 * ---------------------------------------------------------------------------
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

#define MAX_LINEA 1024
#define MAX_CLAVE 128
#define MAX_PILA 32
#define MAX_REDES 128
#define MAX_INTERFACES 4096

typedef struct {
    char nombre[MAX_CLAVE];
    char driver[MAX_CLAVE];
    char subnet[MAX_CLAVE];
    char gateway[MAX_CLAVE];
} Red;

typedef struct {
    char servicio[MAX_CLAVE];
    char red[MAX_CLAVE];
    char ip[MAX_CLAVE];
} Interfaz;

typedef struct {
    int indent;
    char clave[MAX_CLAVE];
} NivelPila;

static Red redes[MAX_REDES];
static int total_redes = 0;

static Interfaz interfaces[MAX_INTERFACES];
static int total_interfaces = 0;

static NivelPila pila[MAX_PILA];
static int tope_pila = 0; /* pila[0] = raiz virtual, indent = -1 */

static int buscar_red(const char *nombre) {
    for (int i = 0; i < total_redes; i++) {
        if (strcmp(redes[i].nombre, nombre) == 0) return i;
    }
    return -1;
}

/* Copia 'origen' a 'destino' (tamano MAX_CLAVE) garantizando terminador nulo,
 * incluso si 'origen' es mas largo que el buffer (se trunca sin desbordar). */
static void copiar_clave(char *destino, const char *origen) {
    snprintf(destino, MAX_CLAVE, "%s", origen);
}

static void set_si_vacio(char *campo, const char *valor) {
    if (valor != NULL) {
        copiar_clave(campo, valor);
    }
}

/* Recorta espacios/CR/LF al final y espacios al inicio; devuelve puntero al
 * primer caracter no-espacio dentro del propio buffer (in place). */
static char *recortar(char *s) {
    size_t len = strlen(s);
    while (len > 0 && (s[len - 1] == '\n' || s[len - 1] == '\r' || s[len - 1] == ' ' || s[len - 1] == '\t')) {
        s[--len] = '\0';
    }
    char *inicio = s;
    while (*inicio == ' ' || *inicio == '\t') inicio++;
    return inicio;
}

/* Analiza una linea cruda. Devuelve 1 si produjo (indent, clave?, valor),
 * 0 si la linea debe ignorarse (vacia o comentario). */
static int analizar_linea(char *linea_cruda, int *indent_out, char clave_out[MAX_CLAVE],
                           int *tiene_clave, char valor_out[MAX_CLAVE], int *tiene_valor) {
    int indent = 0;
    char *p = linea_cruda;
    while (*p == ' ') { indent++; p++; }

    char *contenido = recortar(p);
    if (contenido[0] == '\0' || contenido[0] == '#') return 0;

    if (contenido[0] == '-' && contenido[1] == ' ') {
        contenido += 2;
        while (*contenido == ' ') contenido++;
        indent += 2;
    } else if (contenido[0] == '-' && contenido[1] == '\0') {
        return 0;
    }

    char *dos_puntos = strchr(contenido, ':');
    *indent_out = indent;
    *tiene_clave = 0;
    *tiene_valor = 0;
    clave_out[0] = '\0';
    valor_out[0] = '\0';

    if (dos_puntos != NULL) {
        size_t len_clave = (size_t)(dos_puntos - contenido);
        if (len_clave >= MAX_CLAVE) len_clave = MAX_CLAVE - 1;
        strncpy(clave_out, contenido, len_clave);
        clave_out[len_clave] = '\0';
        char *fin_clave = clave_out + strlen(clave_out);
        while (fin_clave > clave_out && fin_clave[-1] == ' ') *(--fin_clave) = '\0';
        *tiene_clave = 1;

        char *resto = dos_puntos + 1;
        while (*resto == ' ') resto++;
        char *valor_recortado = recortar(resto);
        if (valor_recortado[0] != '\0') {
            copiar_clave(valor_out, valor_recortado);
            *tiene_valor = 1;
        }
    } else {
        copiar_clave(valor_out, contenido);
        *tiene_valor = 1;
    }
    return 1;
}

static void procesar_linea(int indent, const char *clave, int tiene_clave, const char *valor, int tiene_valor) {
    while (tope_pila > 0 && pila[tope_pila - 1].indent >= indent) {
        tope_pila--;
    }

    /* ruta = claves de pila[1..tope_pila-1] + (clave o "*") */
    const char *ruta[MAX_PILA];
    int n = 0;
    for (int i = 1; i < tope_pila; i++) ruta[n++] = pila[i].clave;
    ruta[n++] = tiene_clave ? clave : "*";

    if (n == 2 && strcmp(ruta[0], "networks") == 0 && tiene_clave) {
        if (total_redes < MAX_REDES) {
            Red *r = &redes[total_redes++];
            copiar_clave(r->nombre, ruta[1]);
            copiar_clave(r->driver, "bridge");
            r->subnet[0] = '\0';
            r->gateway[0] = '\0';
        }
    } else if (n == 3 && strcmp(ruta[0], "networks") == 0 && strcmp(ruta[2], "driver") == 0) {
        int idx = buscar_red(ruta[1]);
        if (idx >= 0 && tiene_valor) set_si_vacio(redes[idx].driver, valor);
    } else if (n == 5 && strcmp(ruta[0], "networks") == 0 && strcmp(ruta[2], "ipam") == 0 &&
               strcmp(ruta[3], "config") == 0 && (strcmp(ruta[4], "subnet") == 0 || strcmp(ruta[4], "gateway") == 0)) {
        int idx = buscar_red(ruta[1]);
        if (idx >= 0 && tiene_valor) {
            if (strcmp(ruta[4], "subnet") == 0) set_si_vacio(redes[idx].subnet, valor);
            else set_si_vacio(redes[idx].gateway, valor);
        }
    } else if (n == 4 && strcmp(ruta[0], "services") == 0 && strcmp(ruta[2], "networks") == 0 &&
               strcmp(ruta[3], "*") == 0) {
        if (total_interfaces < MAX_INTERFACES && tiene_valor) {
            Interfaz *iface = &interfaces[total_interfaces++];
            copiar_clave(iface->servicio, ruta[1]);
            copiar_clave(iface->red, valor);
            iface->ip[0] = '\0';
        }
    } else if (n == 4 && strcmp(ruta[0], "services") == 0 && strcmp(ruta[2], "networks") == 0) {
        if (total_interfaces < MAX_INTERFACES) {
            Interfaz *iface = &interfaces[total_interfaces++];
            copiar_clave(iface->servicio, ruta[1]);
            copiar_clave(iface->red, ruta[3]);
            iface->ip[0] = '\0';
        }
    } else if (n == 5 && strcmp(ruta[0], "services") == 0 && strcmp(ruta[2], "networks") == 0 &&
               strcmp(ruta[4], "ipv4_address") == 0) {
        for (int i = total_interfaces - 1; i >= 0; i--) {
            if (strcmp(interfaces[i].servicio, ruta[1]) == 0 && strcmp(interfaces[i].red, ruta[3]) == 0) {
                if (tiene_valor) set_si_vacio(interfaces[i].ip, valor);
                break;
            }
        }
    }

    if (tiene_clave && tope_pila < MAX_PILA) {
        pila[tope_pila].indent = indent;
        copiar_clave(pila[tope_pila].clave, clave);
        tope_pila++;
    }
}

int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "Uso: %s <archivo docker-compose.yml>\n", argv[0]);
        return 1;
    }
    FILE *archivo = fopen(argv[1], "r");
    if (!archivo) {
        perror("No se pudo abrir el archivo");
        return 1;
    }

    pila[0].indent = -1;
    pila[0].clave[0] = '\0';
    tope_pila = 1;

    char linea[MAX_LINEA];
    while (fgets(linea, sizeof(linea), archivo) != NULL) {
        int indent;
        char clave[MAX_CLAVE];
        char valor[MAX_CLAVE];
        int tiene_clave, tiene_valor;
        if (analizar_linea(linea, &indent, clave, &tiene_clave, valor, &tiene_valor)) {
            procesar_linea(indent, clave, tiene_clave, valor, tiene_valor);
        }
    }
    fclose(archivo);

    printf("REDES:\n");
    for (int i = 0; i < total_redes; i++) {
        printf("nombre=%s driver=%s subnet=%s gateway=%s\n",
               redes[i].nombre,
               redes[i].driver[0] ? redes[i].driver : "-",
               redes[i].subnet[0] ? redes[i].subnet : "-",
               redes[i].gateway[0] ? redes[i].gateway : "-");
    }
    printf("\nINTERFACES:\n");
    for (int i = 0; i < total_interfaces; i++) {
        printf("servicio=%s red=%s ip=%s\n",
               interfaces[i].servicio, interfaces[i].red,
               interfaces[i].ip[0] ? interfaces[i].ip : "-");
    }
    return 0;
}
