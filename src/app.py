"""Interfaz Streamlit de GIPP.

Ejecutar desde la raíz del proyecto:
    streamlit run src/app.py
"""
import html as html_lib
import re
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

from github_extractor import (
    GitHubError,
    listar_repos,
    normalizar_usuario,
    obtener_colaboradores,
    obtener_readme,
)
from portafolio import TEMAS
from llm_agents import LLMError, construir_portafolio, redactar_perfil
from portafolio import renderizar_portafolio
from seguridad import (
    en_una_linea,
    limpiar_visible,
    markdown_a_html,
    texto_de_cv,
    validar_contacto,
)

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

st.set_page_config(page_title="GIPP", page_icon="📄", layout="centered")
st.title("GIPP: Generador Inteligente de Portafolios Profesionales")
st.caption("Tú decides qué repos entran y qué se publica. La IA solo redacta con lo que confirmas.")



def sin_markdown(texto):
    return re.sub(r"([\\`*_{}\[\]()#+!<>|~$-])", r"\\\1", limpiar_visible(texto or "", 200))


def vista_previa(documento, alto=430, escala=0.5):
    ancho = int(100 / escala)
    marco = html_lib.escape(documento, quote=True)
    components.html(
        f'<div style="height:{alto}px;overflow:hidden;border:1px solid #8884;border-radius:10px;background:#fff">'
        f'<iframe sandbox="" srcdoc="{marco}" scrolling="no" '
        f'style="width:{ancho}%;height:{int(alto / escala)}px;border:0;transform:scale({escala});'
        'transform-origin:0 0"></iframe></div>',
        height=alto + 8,
    )


ESTILOS_README = """
body { margin: 0; padding: 1rem 1.25rem; font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  line-height: 1.6; color: #1f2328; background: #ffffff; font-size: 15px; }
h1, h2, h3 { line-height: 1.25; margin: 1.2rem 0 0.6rem; }
h1 { font-size: 1.6rem; border-bottom: 1px solid #d8dee4; padding-bottom: 0.3rem; }
h2 { font-size: 1.25rem; border-bottom: 1px solid #d8dee4; padding-bottom: 0.25rem; }
h3 { font-size: 1.05rem; }
p, li { overflow-wrap: anywhere; }
ul, ol { padding-left: 1.4rem; }
hr { border: 0; border-top: 1px solid #d8dee4; margin: 1.2rem 0; }
code { background: #f0f2f4; padding: 0.1rem 0.3rem; border-radius: 4px; font-size: 0.9em; }
pre { background: #f0f2f4; padding: 0.8rem; border-radius: 8px; overflow-x: auto; }
pre code { background: none; padding: 0; }
blockquote { margin: 0.8rem 0; padding: 0.2rem 1rem; border-left: 3px solid #d0d7de; color: #57606a; }
a { color: #0969da; }
.imagen { display: inline-block; padding: 0.1rem 0.5rem; margin: 0.1rem; border: 1px solid #d8dee4;
  border-radius: 999px; font-size: 0.85em; color: #57606a; }
@media (prefers-color-scheme: dark) {
  body { color: #e6edf3; background: #0d1117; }
  h1, h2, hr { border-color: #30363d; }
  code, pre { background: #161b22; }
  blockquote { border-color: #30363d; color: #8b949e; }
  a { color: #58a6ff; }
  .imagen { border-color: #30363d; color: #8b949e; }
}
"""


def vista_readme(texto, alto=420):
    documento = (
        "<!DOCTYPE html><html lang=\"es\"><head><meta charset=\"utf-8\">"
        "<meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'none'; "
        "style-src 'unsafe-inline'; img-src data:\">"
        f"<style>{ESTILOS_README}</style></head><body>{markdown_a_html(texto)}</body></html>"
    )
    components.html(
        f'<iframe sandbox="" srcdoc="{html_lib.escape(documento, quote=True)}" '
        f'style="width:100%;height:{alto}px;border:1px solid #8884;border-radius:10px;background:transparent"></iframe>',
        height=alto + 8,
    )


def mover_plantilla(paso):
    st.session_state.indice_plantilla = (st.session_state.indice_plantilla + paso) % len(TEMAS)


for clave in ("usuario", "repos", "perfil", "html", "sobre_mi", "alertas", "avisos", "elegidos"):
    st.session_state.setdefault(clave, None)

# ---------- 1. Usuario de GitHub ----------
st.header("1. Usuario de GitHub")
with st.form("buscar"):
    entrada = st.text_input("Usuario o URL de GitHub", placeholder="https://github.com/usuario")
    buscar = st.form_submit_button("Buscar repositorios")

if buscar:
    try:
        usuario = normalizar_usuario(entrada)
        with st.spinner("Consultando GitHub..."):
            repos = listar_repos(usuario)
            # README del perfil (usuario/usuario); vacío si no existe. 1 petición extra.
            st.session_state.sobre_mi = obtener_readme(usuario, usuario)
        st.session_state.usuario = usuario
        st.session_state.repos = repos
        st.session_state.perfil = None
        st.session_state.html = None
        st.session_state.pop("perfil_editado", None)
    except (ValueError, GitHubError) as exc:
        st.error(str(exc))

repos = st.session_state.repos
if repos is not None and not repos:
    st.warning("Este usuario no tiene repositorios públicos propios.")

# ---------- 2. Selección de repos y roles ----------
if repos:
    st.header("2. Repositorios a incluir")
    sobre_mi = st.session_state.sobre_mi
    if sobre_mi:
        with st.expander("Tu README de perfil (presentación y herramientas)", expanded=True):
            vista_readme(sobre_mi)
        incluir_sobre_mi = st.checkbox(
            "Incluir mi README de perfil (presentación y herramientas)",
            value=True,
        )
        if not incluir_sobre_mi:
            sobre_mi = None
    else:
        sobre_mi = None

    st.subheader("Currículum (opcional)")
    st.caption(
        "Si subes tu CV (PDF, DOCX, TXT o MD), el modelo lo usa como contexto para redactar. "
        "Se procesa en memoria y no se guarda."
    )
    archivo_cv = st.file_uploader("Sube tu CV", type=["pdf", "docx", "txt", "md"], key="archivo_cv")
    cv_texto = st.session_state.get("cv_texto")
    if archivo_cv is not None:
        try:
            cv_texto = texto_de_cv(archivo_cv.name, archivo_cv.getvalue())
            st.session_state.cv_texto = cv_texto
            st.session_state.cv_nombre = archivo_cv.name
            st.session_state.cv_archivo = archivo_cv.getvalue()
        except ValueError as exc:
            cv_texto = None
            st.session_state.cv_texto = None
            st.session_state.cv_archivo = None
            st.error(str(exc))
    if cv_texto:
        st.success(f"CV leído: {st.session_state.get('cv_nombre', 'archivo')} ({len(cv_texto)} caracteres).")
        with st.expander("Ver el texto que se enviará al modelo"):
            st.text(cv_texto[:4000])
        if not st.checkbox("Incluir mi CV al redactar el perfil", value=True, key="incluir_cv"):
            cv_texto = None
        if (st.session_state.get("cv_nombre") or "").lower().endswith(".pdf"):
            st.checkbox(
                "Ofrecer el PDF para descargar en la sección de contacto del portafolio",
                value=True,
                key="cv_descargable",
            )
    else:
        cv_texto = None

    with st.form("seleccion"):
        for i, r in enumerate(repos):
            st.checkbox(f"**{sin_markdown(r['name'])}** · {sin_markdown(r['language'] or 'sin lenguaje')}", key=f"inc_{i}")
            if r["description"]:
                st.caption(sin_markdown(r["description"]))
            st.text_input("¿En qué trabajaste? (opcional)", key=f"nota_{i}")
        generar = st.form_submit_button("Generar perfil con los repos seleccionados")

    if generar:
        elegidos = []
        for i, r in enumerate(repos):
            if st.session_state.get(f"inc_{i}"):
                elegido = dict(r)
                elegido["nota_usuario"] = st.session_state.get(f"nota_{i}", "").strip()
                elegidos.append(elegido)

        if not elegidos:
            st.error("Selecciona al menos un repositorio.")
        else:
            try:
                # El README se pide solo para los repos seleccionados (ahorra peticiones).
                with st.spinner("Leyendo READMEs y redactando el perfil..."):
                    for elegido in elegidos:
                        elegido["readme"] = obtener_readme(st.session_state.usuario, elegido["name"])
                        elegido["colaboradores"] = obtener_colaboradores(
                            st.session_state.usuario, elegido["name"]
                        )
                    perfil, alertas = redactar_perfil(
                        st.session_state.usuario, elegidos, sobre_mi, cv_texto
                    )
                st.session_state.sobre_mi_usado = sobre_mi
                st.session_state.perfil = perfil
                st.session_state.alertas = alertas
                st.session_state.elegidos = elegidos
                st.session_state.avisos = None
                st.session_state.html = None
                st.session_state.perfil_editado = perfil
            except LLMError as exc:
                st.error(str(exc))

# ---------- 3. Revisión humana del perfil ----------
if st.session_state.perfil:
    st.header("3. Revisa y edita el perfil")
    if st.session_state.alertas:
        st.warning(
            "Alertas de seguridad: algún texto de tus repos parecía una instrucción dirigida a la IA "
            "o el perfil incluye enlaces que no están en tus datos. Revisa con cuidado."
        )
        for alerta in st.session_state.alertas:
            st.write(f"- {limpiar_visible(alerta, 300)}")
    st.text_area("Perfil generado", key="perfil_editado", height=260)
    st.info("Revisa que todo lo escrito sea cierto. Corrige lo que no lo sea antes de continuar.")

    st.subheader("Contacto (opcional)")
    st.caption(
        "Lo escribes tú: la IA no lo ve ni lo modifica. Lo que pongas será público en tu portafolio."
    )
    columna_correo, columna_linkedin = st.columns(2)
    correo = columna_correo.text_input("Correo", key="contacto_correo", placeholder="nombre@dominio.com")
    linkedin = columna_linkedin.text_input(
        "LinkedIn", key="contacto_linkedin", placeholder="https://www.linkedin.com/in/tu-usuario"
    )
    contacto, errores_contacto = validar_contacto(correo, linkedin)
    for error in errores_contacto:
        st.error(error)

    cv_para_pagina = None
    if st.session_state.get("cv_descargable") and st.session_state.get("cv_archivo"):
        cv_para_pagina = {
            "nombre": st.session_state.get("cv_nombre"),
            "contenido": st.session_state.cv_archivo,
        }

    st.subheader("Elige la plantilla")
    st.session_state.setdefault("indice_plantilla", 0)
    plantilla = list(TEMAS)[st.session_state.indice_plantilla]
    izquierda, centro, derecha = st.columns([1, 4, 1])
    izquierda.button("◀", key="plantilla_anterior", on_click=mover_plantilla, args=(-1,), use_container_width=True)
    derecha.button("▶", key="plantilla_siguiente", on_click=mover_plantilla, args=(1,), use_container_width=True)
    centro.markdown(
        f"<div style='text-align:center'><b>{html_lib.escape(TEMAS[plantilla][0])}</b><br>"
        f"{st.session_state.indice_plantilla + 1} de {len(TEMAS)}</div>",
        unsafe_allow_html=True,
    )
    try:
        proyectos_previa = [
            {
                "name": en_una_linea(r.get("name"), 100),
                "language": en_una_linea(r.get("language"), 40) or None,
                "description": en_una_linea(r.get("description"), 200) or None,
                "url": r.get("html_url") or r.get("url"),
            }
            for r in st.session_state.elegidos or []
        ]
        vista_previa(
            renderizar_portafolio(
                st.session_state.usuario,
                "",
                "",
                limpiar_visible(st.session_state.perfil_editado or "", 4000),
                [],
                proyectos_previa,
                plantilla,
                contacto,
                cv_para_pagina,
            )
        )
    except ValueError:
        st.warning("No se pudo generar la vista previa.")

    if st.button(f"Aprobar y generar portafolio con «{TEMAS[plantilla][0]}»", type="primary"):
        perfil_final = st.session_state.perfil_editado.strip()
        if not perfil_final:
            st.error("El perfil está vacío.")
        elif errores_contacto:
            st.error("Corrige los datos de contacto o déjalos vacíos para continuar.")
        else:
            try:
                with st.spinner("Generando la página..."):
                    html, avisos = construir_portafolio(
                        st.session_state.usuario,
                        perfil_final,
                        st.session_state.elegidos,
                        st.session_state.get("sobre_mi_usado"),
                        plantilla,
                        contacto,
                        cv_para_pagina,
                    )
                    st.session_state.html = html
                    st.session_state.avisos = avisos
            except LLMError as exc:
                st.error(str(exc))

# ---------- 4. Resultado ----------
if st.session_state.html:
    st.header("4. Portafolio")
    for aviso in st.session_state.avisos or []:
        st.warning(limpiar_visible(aviso, 300))
    st.download_button(
        "Descargar portafolio HTML",
        data=st.session_state.html.encode("utf-8"),
        file_name=f"portafolio_{st.session_state.usuario}.html",
        mime="text/html",
    )
    st.caption("Vista previa: página generada con plantilla fija, sin scripts ni recursos externos.")
    components.html(st.session_state.html, height=600, scrolling=True)
