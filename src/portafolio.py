"""Renderiza el portafolio HTML a partir de datos ya validados."""

import html
import re

ESTILOS_CSS = """
:root {
  --fondo: #f6f7f9;
  --tarjeta: #ffffff;
  --texto: #1b1f24;
  --atenuado: #55606e;
  --borde: #e3e6eb;
  --acento: #2850c8;
  --acento-oscuro: #1f409e;
}

@media (prefers-color-scheme: dark) {
  :root {
    --fondo: #0e1318;
    --tarjeta: #161d26;
    --texto: #e7eaef;
    --atenuado: #a2adba;
    --borde: #26303c;
    --acento: #8fb0ff;
    --acento-oscuro: #4a6fd6;
  }
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  background: var(--fondo);
  color: var(--texto);
  font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  line-height: 1.6;
}

a {
  color: var(--acento);
  text-decoration: none;
  transition: color 0.15s ease;
}

a:hover {
  text-decoration: underline;
}

:focus-visible {
  outline: 3px solid var(--acento);
  outline-offset: 2px;
}

.contenedor {
  max-width: 860px;
  margin: 0 auto;
  padding: 0 1.5rem;
}

.saltar {
  position: fixed;
  top: 0.75rem;
  left: 0.75rem;
  z-index: 100;
  padding: 0.5rem 0.9rem;
  border-radius: 6px;
  background: var(--acento);
  color: #ffffff;
  font-weight: 600;
  text-decoration: none;
  transform: translateY(calc(-100% - 2rem));
  transition: transform 0.15s ease;
}

.saltar:focus,
.saltar:focus-visible {
  transform: translateY(0);
}

.hero {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  padding: 3rem 0 2rem;
}

.avatar {
  flex-shrink: 0;
  width: 72px;
  height: 72px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--acento), var(--acento-oscuro));
  color: #ffffff;
  font-size: 1.6rem;
  font-weight: 700;
  letter-spacing: 0.03em;
}

.hero-texto {
  min-width: 0;
}

.hero h1 {
  margin: 0;
  font-size: 2rem;
  line-height: 1.2;
  overflow-wrap: break-word;
}

.titular {
  margin: 0.35rem 0 0;
  color: var(--atenuado);
  font-size: 1.05rem;
}

.enlace-github {
  margin: 0.7rem 0 0;
  font-size: 0.95rem;
}

.seccion {
  border-top: 1px solid var(--borde);
  padding: 2rem 0;
}

.seccion h2 {
  margin: 0 0 1.1rem;
  font-size: 1.3rem;
}

.sobre-mi p {
  line-height: 1.7;
  max-width: 70ch;
  margin: 0 0 0.9rem;
}

.sobre-mi p:last-child {
  margin-bottom: 0;
}

.chips {
  list-style: none;
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin: 0;
  padding: 0;
}

.chips li {
  border: 1px solid var(--borde);
  background: var(--tarjeta);
  border-radius: 999px;
  padding: 0.35rem 0.9rem;
  font-size: 0.9rem;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1rem;
}

.tarjeta {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  background: var(--tarjeta);
  border: 1px solid var(--borde);
  border-radius: 12px;
  padding: 1.25rem;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.tarjeta:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08);
}

.titulo-proyecto {
  margin: 0;
  font-size: 1.05rem;
  line-height: 1.35;
  overflow-wrap: break-word;
}

.lenguaje {
  margin: 0;
}

.chip-lenguaje {
  display: inline-block;
  border: 1px solid var(--borde);
  border-radius: 999px;
  padding: 0.12rem 0.55rem;
  font-size: 0.8rem;
  color: var(--atenuado);
}

.descripcion {
  margin: 0;
  color: var(--atenuado);
  font-size: 0.95rem;
  overflow-wrap: break-word;
}

footer {
  border-top: 1px solid var(--borde);
  color: var(--atenuado);
  font-size: 0.85rem;
  padding: 1.25rem 0 2.5rem;
}

footer p {
  margin: 0;
}

@media (max-width: 560px) {
  .contenedor {
    padding-left: 1rem;
    padding-right: 1rem;
  }

  .hero {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
    padding-top: 2rem;
  }
}

@media (prefers-reduced-motion: reduce) {
  .saltar,
  .tarjeta,
  a {
    transition: none;
  }
}

@media print {
  body {
    background: #ffffff;
    color: #000000;
  }

  .titular,
  .descripcion,
  .chip-lenguaje,
  footer {
    color: #333333;
  }

  .tarjeta,
  .chips li {
    background: #ffffff;
  }

  .seccion,
  .tarjeta,
  .chips li {
    border-color: #c8ccd2;
  }

  .tarjeta {
    box-shadow: none;
    break-inside: avoid;
  }

  a {
    color: #1f409e;
    text-decoration: underline;
  }

  .saltar {
    display: none;
  }
}
"""

PLANTILLA_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="referrer" content="no-referrer">
<title><TITULO> · Portafolio</title>
<style>
<CSS>
</style>
</head>
<body>
<a class="saltar" href="#contenido">Saltar al contenido</a>
<div class="contenedor">
<header class="hero">
  <div class="avatar" aria-hidden="true"><INICIALES></div>
  <div class="hero-texto">
    <h1><NOMBRE></h1>
    <TITULAR>
    <p class="enlace-github"><a href="<URL_USUARIO>"><USUARIO_TEXTO></a></p>
  </div>
</header>
<main id="contenido">
<SECCIONES>
</main>
<footer>
  <p>Portafolio generado con GIPP. El texto fue revisado y aprobado por su autor.</p>
</footer>
</div>
</body>
</html>
"""


def renderizar_portafolio(usuario: str, nombre: str, titular: str, resumen: str,
                          habilidades: list[str], proyectos: list[dict]) -> str:
    """Genera el HTML del portafolio a partir de datos ya validados."""
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]{0,38}", usuario):
        raise ValueError("Usuario de GitHub no válido.")
    nombre_final = nombre.strip() or usuario
    titular = titular.strip()

    iniciales = ""
    for palabra in nombre_final.split():
        if palabra[0].isalpha():
            iniciales += palabra[0].upper()
            if len(iniciales) == 2:
                break
    if not iniciales:
        iniciales = usuario[0].upper()

    secciones = []
    parrafos = []
    for bloque in re.split(r"\n\s*\n", resumen):
        texto = " ".join(bloque.split())
        if texto:
            parrafos.append("<p>" + html.escape(texto) + "</p>")
    if parrafos:
        secciones.append(
            '<section class="seccion sobre-mi" aria-labelledby="sobre-mi">'
            '<h2 id="sobre-mi">Sobre mí</h2>'
            + "".join(parrafos)
            + "</section>"
        )

    chips = [
        "<li>" + html.escape(habilidad.strip()) + "</li>"
        for habilidad in habilidades
        if habilidad.strip()
    ]
    if chips:
        secciones.append(
            '<section class="seccion" aria-labelledby="habilidades">'
            '<h2 id="habilidades">Habilidades y herramientas</h2>'
            '<ul class="chips">' + "".join(chips) + "</ul>"
            "</section>"
        )

    tarjetas = []
    prefijo_url = "https://github.com/" + usuario + "/"
    for proyecto in proyectos:
        nombre_proyecto = html.escape(proyecto.get("name") or "")
        url = proyecto.get("url")
        lenguaje = proyecto.get("language") or None
        descripcion = proyecto.get("description") or None
        if isinstance(url, str) and url.startswith(prefijo_url):
            cabecera = (
                '<h3 class="titulo-proyecto">'
                f'<a href="{html.escape(url)}" target="_blank" rel="noopener noreferrer">'
                f"{nombre_proyecto}</a></h3>"
            )
        else:
            cabecera = '<h3 class="titulo-proyecto">' + nombre_proyecto + "</h3>"
        piezas = [cabecera]
        if lenguaje:
            piezas.append(
                '<p class="lenguaje"><span class="chip-lenguaje">'
                + html.escape(lenguaje)
                + "</span></p>"
            )
        if descripcion:
            piezas.append(
                '<p class="descripcion">' + html.escape(descripcion) + "</p>"
            )
        tarjetas.append('<article class="tarjeta">' + "".join(piezas) + "</article>")
    if tarjetas:
        secciones.append(
            '<section class="seccion" aria-labelledby="proyectos">'
            '<h2 id="proyectos">Proyectos</h2>'
            '<div class="grid">' + "".join(tarjetas) + "</div>"
            "</section>"
        )

    nombre_escapado = html.escape(nombre_final)
    titular_html = ""
    if titular:
        titular_html = '<p class="titular">' + html.escape(titular) + "</p>"
    return (
        PLANTILLA_HTML
        .replace("<CSS>", ESTILOS_CSS)
        .replace("<TITULO>", nombre_escapado)
        .replace("<NOMBRE>", nombre_escapado)
        .replace("<TITULAR>", titular_html)
        .replace("<INICIALES>", html.escape(iniciales))
        .replace("<URL_USUARIO>", html.escape("https://github.com/" + usuario))
        .replace("<USUARIO_TEXTO>", html.escape("github.com/" + usuario))
        .replace("<SECCIONES>", "".join(secciones))
    )
