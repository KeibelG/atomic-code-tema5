// Lenguaje:   Rust
// Asignatura: Lenguajes y compiladores
// Equipo:     Atomic Code
//             Segmentando el codigo, construyendo la logica
//
// Integrantes:
//   - Victor Vargas    C.I: 30.697.219
//   - Keibel Guilarte  C.I: 28.726.605
//   - Oriana Marquez   C.I: 31.354.299
//   - Jeanny Monagas   C.I: 30.857.471
//
// ---------------------------------------------------------------------------
//                           DESCRIPCION
// ---------------------------------------------------------------------------
// Version en Rust del lexer + parser de interfaces de red de Docker Compose.
// Mismo algoritmo y mismo formato de salida que python/compose_netparser.py
// y c/compose_netparser.c, para que el experimento de tiempos compare
// directamente la implementacion del mismo analisis en tres lenguajes.
//
// Lexico por linea: se ignoran lineas en blanco y comentarios ('#'). Cada
// linea se clasifica en indentacion efectiva, clave y valor (o solo valor si
// es un escalar suelto de una lista, ej. '- frontend').
//
// Sintactico: se mantiene una pila de (indentacion, clave) que reconstruye la
// ruta de claves ancestras de cada linea; contra esa ruta se contrastan los
// mismos patrones fijos de 'services.<svc>.networks' y 'networks.<red>...'.
//
// Uso:      compose_netparser.exe archivo.yml
// ---------------------------------------------------------------------------

use std::env;
use std::fs;
use std::process;

struct Red {
    nombre: String,
    driver: String,
    subnet: Option<String>,
    gateway: Option<String>,
}

struct Interfaz {
    servicio: String,
    red: String,
    ip: Option<String>,
}

/// Analiza una linea cruda: (indentacion, clave_opcional, valor_opcional).
/// Devuelve None si la linea debe ignorarse (vacia o comentario).
fn analizar_linea(linea_cruda: &str) -> Option<(usize, Option<String>, Option<String>)> {
    let sin_salto = linea_cruda.trim_end_matches(['\n', '\r']);
    let indent_base = sin_salto.len() - sin_salto.trim_start_matches(' ').len();
    let mut contenido = sin_salto.trim();
    let mut indent = indent_base;

    if contenido.is_empty() || contenido.starts_with('#') {
        return None;
    }

    if let Some(resto) = contenido.strip_prefix("- ") {
        contenido = resto.trim_start();
        indent += 2;
    } else if contenido == "-" {
        return None;
    }

    if let Some(pos) = contenido.find(':') {
        let clave = contenido[..pos].trim().to_string();
        let valor = contenido[pos + 1..].trim();
        let valor_opt = if valor.is_empty() { None } else { Some(valor.to_string()) };
        Some((indent, Some(clave), valor_opt))
    } else {
        Some((indent, None, Some(contenido.trim().to_string())))
    }
}

fn buscar_red<'a>(redes: &'a mut [Red], nombre: &str) -> Option<&'a mut Red> {
    redes.iter_mut().find(|r| r.nombre == nombre)
}

fn analizar_compose(texto: &str) -> (Vec<Red>, Vec<Interfaz>) {
    let mut redes: Vec<Red> = Vec::new();
    let mut interfaces: Vec<Interfaz> = Vec::new();

    // pila de (indentacion, clave); primer elemento = raiz virtual (-1)
    let mut pila: Vec<(i64, String)> = vec![(-1, String::new())];

    for linea_cruda in texto.lines() {
        let analizado = match analizar_linea(linea_cruda) {
            Some(valor) => valor,
            None => continue,
        };
        let (indent, clave_opt, valor_opt) = analizado;
        let indent = indent as i64;

        while pila.last().map(|(i, _)| *i >= indent).unwrap_or(false) {
            pila.pop();
        }

        let mut ruta: Vec<String> = pila[1..].iter().map(|(_, k)| k.clone()).collect();
        ruta.push(clave_opt.clone().unwrap_or_else(|| "*".to_string()));

        match ruta.len() {
            2 if ruta[0] == "networks" && clave_opt.is_some() => {
                redes.push(Red {
                    nombre: ruta[1].clone(),
                    driver: "bridge".to_string(),
                    subnet: None,
                    gateway: None,
                });
            }
            3 if ruta[0] == "networks" && ruta[2] == "driver" => {
                if let Some(red) = buscar_red(&mut redes, &ruta[1]) {
                    if let Some(valor) = &valor_opt {
                        red.driver = valor.clone();
                    }
                }
            }
            5 if ruta[0] == "networks" && ruta[2] == "ipam" && ruta[3] == "config"
                && (ruta[4] == "subnet" || ruta[4] == "gateway") =>
            {
                if let Some(red) = buscar_red(&mut redes, &ruta[1]) {
                    if ruta[4] == "subnet" {
                        red.subnet = valor_opt.clone();
                    } else {
                        red.gateway = valor_opt.clone();
                    }
                }
            }
            4 if ruta[0] == "services" && ruta[2] == "networks" && ruta[3] == "*" => {
                if let Some(valor) = &valor_opt {
                    interfaces.push(Interfaz {
                        servicio: ruta[1].clone(),
                        red: valor.clone(),
                        ip: None,
                    });
                }
            }
            4 if ruta[0] == "services" && ruta[2] == "networks" => {
                interfaces.push(Interfaz {
                    servicio: ruta[1].clone(),
                    red: ruta[3].clone(),
                    ip: None,
                });
            }
            5 if ruta[0] == "services" && ruta[2] == "networks" && ruta[4] == "ipv4_address" => {
                if let Some(iface) = interfaces
                    .iter_mut()
                    .rev()
                    .find(|i| i.servicio == ruta[1] && i.red == ruta[3])
                {
                    iface.ip = valor_opt.clone();
                }
            }
            _ => {}
        }

        if let Some(clave) = clave_opt {
            pila.push((indent, clave));
        }
    }

    (redes, interfaces)
}

fn formatear_salida(redes: &[Red], interfaces: &[Interfaz]) -> String {
    let mut salida = String::from("REDES:\n");
    for red in redes {
        salida.push_str(&format!(
            "nombre={} driver={} subnet={} gateway={}\n",
            red.nombre,
            if red.driver.is_empty() { "-" } else { &red.driver },
            red.subnet.as_deref().unwrap_or("-"),
            red.gateway.as_deref().unwrap_or("-"),
        ));
    }
    salida.push('\n');
    salida.push_str("INTERFACES:\n");
    for iface in interfaces {
        salida.push_str(&format!(
            "servicio={} red={} ip={}\n",
            iface.servicio,
            iface.red,
            iface.ip.as_deref().unwrap_or("-"),
        ));
    }
    salida
}

fn main() {
    let argumentos: Vec<String> = env::args().collect();
    if argumentos.len() != 2 {
        eprintln!("Uso: {} <archivo docker-compose.yml>", argumentos[0]);
        process::exit(1);
    }

    let texto = match fs::read_to_string(&argumentos[1]) {
        Ok(contenido) => contenido,
        Err(error) => {
            eprintln!("No se pudo abrir el archivo: {}", error);
            process::exit(1);
        }
    };

    let (redes, interfaces) = analizar_compose(&texto);
    let salida = formatear_salida(&redes, &interfaces);
    print!("{}", salida.trim_end_matches('\n'));
    println!();
}
