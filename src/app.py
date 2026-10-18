"""Interfaz Streamlit de GIPP.

Ejecutar desde la raíz del proyecto:
    streamlit run src/app.py
"""
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

from github_extractor import GitHubError, listar_repos, normalizar_usuario, obtener_readme
from llm_agents import LLMError, construir_html, redactar_perfil

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

st.set_page_config(page_title="GIPP", page_icon="📄", layout="centered")
st.title("GIPP: Generador Inteligente de Portafolios Profesionales")
st.caption("Tú decides qué repos entran y qué se publica. La IA solo redacta con lo que confirmas.")

for clave in ("usuario", "repos", "perfil", "html", "sobre_mi"):
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
            st.checkbox(f"**{r['name']}** · {r['language'] or 'sin lenguaje'}", key=f"inc_{i}")
            if r["description"]:
                st.caption(r["description"])
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
                    perfil = redactar_perfil(st.session_state.usuario, elegidos, sobre_mi)
                st.session_state.sobre_mi_usado = sobre_mi
                st.session_state.perfil = perfil
                st.session_state.html = None
                st.session_state.perfil_editado = perfil
            except LLMError as exc:
                st.error(str(exc))

# ---------- 3. Revisión humana del perfil ----------
if st.session_state.perfil:
    st.header("3. Revisa y edita el perfil")
    st.text_area("Perfil generado", key="perfil_editado", height=260)
    st.info("Revisa que todo lo escrito sea cierto. Corrige lo que no lo sea antes de continuar.")

    if st.button("Aprobar y generar portafolio"):
        perfil_final = st.session_state.perfil_editado.strip()
        if not perfil_final:
            st.error("El perfil está vacío.")
        else:
            try:
                with st.spinner("Generando la página..."):
                    st.session_state.html = construir_html(
                        st.session_state.usuario, perfil_final, st.session_state.get("sobre_mi_usado")
                    )
            except LLMError as exc:
                st.error(str(exc))

# ---------- 4. Resultado ----------
if st.session_state.html:
    st.header("4. Portafolio")
    st.download_button(
        "Descargar portafolio HTML",
        data=st.session_state.html.encode("utf-8"),
        file_name=f"portafolio_{st.session_state.usuario}.html",
        mime="text/html",
    )
    st.caption("Vista previa (el HTML generado se revisa antes de publicarlo):")
    components.html(st.session_state.html, height=600, scrolling=True)
