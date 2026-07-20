# Tema 5 - Análisis Sintáctico

### Equipo: **Atomic Code**
> _Segmentando el código, construyendo la lógica_

**Asignatura:** Lenguaje y Compiladores - 2026-I

**Universidad Nacional Experimental de Guayana (UNEG)**

---

## Integrantes

| Integrante | Cédula de Identidad |
|------------|---------------------|
| Victor Vargas | 30.697.219 |
| Keibel Guilarte | 28.726.605 |
| Oriana Márquez | 31.354.299 |
| Jeanny Monagas | 30.857.471 |

---

## Alcance de este repositorio

Este repositorio contiene el **código** de las preguntas 1, 2, 4 y 5 de la actividad del
tema (árbol de sintaxis abstracta, parsers LL y LR, lexer/parser de Docker Compose con
experimento de tiempos, y el asistente híbrido UnegScript).

## Estructura

```
Tema 5 - Lenguajes y compiladores - Atomic Code/
├── 1-AST - Atomic Code/
│   └── ast_ejemplo.py          Pregunta 1: AST, dos ejemplos de entrada
├── 2-LL-LR - Atomic Code/
│   ├── ast_nodes.py            nodos de AST y léxico compartidos
│   ├── ll_parser.py            Pregunta 2: parser LL(1) descendente
│   ├── lr_parser.py            Pregunta 2: generador SLR(1) + parser LR
│   └── demo_ll_lr.py           compara ambos sobre el mismo lenguaje L
├── 4-Docker-Compose - Atomic Code/
│   ├── c/compose_netparser.c        Pregunta 4: implementación en C
│   ├── rust/                        Pregunta 4: implementación en Rust (proyecto cargo)
│   ├── python/compose_netparser.py  Pregunta 4: implementación en Python
│   ├── generar_muestras.py          genera las 12 muestras docker-compose.yml
│   ├── muestras/                    las 12 muestras generadas
│   ├── ejecutar_experimento.py      compila, verifica y mide tiempos -> resultados.csv
│   ├── graficar_resultados.py       resultados.csv -> resultados_tiempos.png
│   ├── directorio_base.py           ubica la carpeta de trabajo (script normal o .exe)
│   ├── ejecutar_todo.py             corre los 3 pasos anteriores en un solo comando
│   └── ejecutar_todo.exe            el mismo ejecutar_todo.py empaquetado como .exe
└── 5-UnegScript - Atomic Code/
    ├── motor_ia_simulado.py    confianza (difflib) + sugerencias, aislado y sustituible
    ├── lexer_hibrido.py        Pregunta 5.1: lexer regex/AFD + fallback a IA
    ├── parser_recursivo.py     Pregunta 5.2: descendente con lookahead + consulta IA
    └── unegscript.py           Pregunta 5.3/5.4: punto de entrada y ejemplo del enunciado
```

## Requisitos

- **Python 3.10+** (sin dependencias externas, salvo `matplotlib` solo para
  `graficar_resultados.py`: `pip install matplotlib`).
- **gcc** (cualquier toolchain moderno; se probó con MSYS2 ucrt64) para la parte en C.
- **Rust** (`rustc` + `cargo`) para la parte en Rust.

## Cómo ejecutar cada parte

**Pregunta 1 (AST):**
```bash
python "1-AST - Atomic Code/ast_ejemplo.py"
```

**Pregunta 2 (LL y LR):**
```bash
python "2-LL-LR - Atomic Code/demo_ll_lr.py"
```

**Pregunta 4 (Docker Compose, 3 lenguajes + experimento de tiempos):**
```bash
cd "4-Docker-Compose - Atomic Code"
python generar_muestras.py        # genera las 12 muestras en muestras/
python ejecutar_experimento.py    # compila C y Rust, verifica consistencia, mide tiempos
python graficar_resultados.py     # produce resultados_tiempos.png
```
`ejecutar_experimento.py` compila automáticamente `c/compose_netparser.c` (con `gcc`) y
`rust/` (con `cargo build --release`); no hace falta compilarlos a mano. Antes de medir
tiempos, el script verifica que las 3 implementaciones extraigan exactamente la misma
información de cada muestra.

**Atajo:** en vez de correr los 3 scripts anteriores por separado, `ejecutar_todo.py` (o
su versión ya compilada `ejecutar_todo.exe`) hace los 3 pasos en un solo comando:
```bash
python "4-Docker-Compose - Atomic Code/ejecutar_todo.py"
```
o, en Windows, doble clic en `4-Docker-Compose - Atomic Code/ejecutar_todo.exe` (debe
quedarse en esa misma carpeta, junto a `c/`, `rust/`, `python/` y `muestras/`; sigue
necesitando `gcc` y `cargo` instalados en la máquina, además de un `python` en el PATH,
porque el `.exe` solo empaqueta la lógica que orquesta los 3 pasos, no los compiladores).

Para regenerar `ejecutar_todo.exe` después de modificar el código:
```bash
pip install pyinstaller
cd "4-Docker-Compose - Atomic Code"
pyinstaller --onefile --name ejecutar_todo --console ejecutar_todo.py
cp dist/ejecutar_todo.exe .
rm -rf build dist ejecutar_todo.spec
```

**Pregunta 5 (UnegScript):**
```bash
python "5-UnegScript - Atomic Code/unegscript.py"
```
Corre por defecto el ejemplo del enunciado
(`pront x = 5; if x > 3 prnt(x) else prnt("no")`). También acepta código propio:
```bash
python "5-UnegScript - Atomic Code/unegscript.py" "x = 1; if x == 1 print(x) esle print(0)"
```

## Notas de diseño

- **Q2 (LL/LR):** ambos parsers reconocen el mismo lenguaje L (expresiones aritméticas
  con `+ - * /` y paréntesis); `lr_parser.py` no tiene la tabla SLR(1) escrita a mano,
  la calcula un generador genérico (cierre/goto de ítems LR(0), FIRST/FOLLOW, ACTION/GOTO)
  a partir de la gramática, igual que lo haría Bison/Yacc por dentro.
- **Q4 (Docker Compose):** el lexer/parser reconoce un subconjunto acotado de Docker
  Compose (bloques `services` y `networks`, con indentación uniforme de 2 espacios),
  documentado en el encabezado de cada implementación; no es un parser YAML general.
- **Q5 (UnegScript):** el "motor de IA" es una simulación local (`motor_ia_simulado.py`)
  basada en `difflib`/Levenshtein, tal como describe la sección 6.2 del enunciado del
  tema; no depende de red ni de API keys, y queda aislada en su propio módulo para poder
  sustituirse por una API real sin tocar el lexer ni el parser.
