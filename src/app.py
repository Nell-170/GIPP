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
from seguridad import en_una_linea, limpiar_visible

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
        with st.expander("Tu README de perfil (presentación y herramientas)"):
            st.text(sobre_mi)
        incluir_sobre_mi = st.checkbox(
            "Incluir mi README de perfil (presentación y herramientas)",
            value=True,
        )
        if not incluir_sobre_mi:
            sobre_mi = None
    else:
        sobre_mi = None

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
                    perfil, alertas = redactar_perfil(st.session_state.usuario, elegidos, sobre_mi)
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
            )
        )
    except ValueError:
        st.warning("No se pudo generar la vista previa.")

    if st.button(f"Aprobar y generar portafolio con «{TEMAS[plantilla][0]}»", type="primary"):
        perfil_final = st.session_state.perfil_editado.strip()
        if not perfil_final:
            st.error("El perfil está vacío.")
        else:
            try:
                with st.spinner("Generando la página..."):
                    html, avisos = construir_portafolio(
                        st.session_state.usuario,
                        perfil_final,
                        st.session_state.elegidos,
                        st.session_state.get("sobre_mi_usado"),
                        plantilla,
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
