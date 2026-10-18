"""Agentes de redacción y construcción, vía API de Abacus.AI (RouteLLM, compatible con OpenAI).

Variables de entorno:
    ABACUS_API_KEY   (obligatoria)
    ABACUS_BASE_URL  (opcional, por defecto DEFAULT_BASE_URL)
    ABACUS_MODEL     (opcional, por defecto DEFAULT_MODEL)
"""
import os
import re

from openai import OpenAI, OpenAIError

DEFAULT_BASE_URL = "https://routellm.abacus.ai/v1"  # verificar en la documentación de Abacus
DEFAULT_MODEL = "gpt-4o"  # ajustar al modelo disponible en la cuenta


class LLMError(Exception):
    """Error controlado al llamar al modelo."""


SYSTEM_REDACTOR = (
    "Eres un redactor de perfiles profesionales para desarrolladores. "
    "Recibes datos de proyectos de GitHub y escribes un perfil profesional en español, "
    "en primera persona, como si lo hubiera escrito la propia persona dueña del perfil. "
    "TONO Y ESTILO (obligatorio): natural, sobrio y concreto, como escribe una persona real "
    "en su portafolio. Prohibido el lenguaje promocional y las frases hechas típicas de IA: "
    "'talentoso', 'sólida experiencia', 'rol integral', 'desempeñó un papel fundamental', "
    "'tecnologías avanzadas', 'alto impacto', 'apasionado', 'versátil', 'excelencia técnica', "
    "'bien posicionado', 'contribuir significativamente'. No elogies a la persona ni uses "
    "adjetivos vacíos: los hechos concretos hablan solos. Varia el largo de las frases y no "
    "empieces varios párrafos con el mismo patrón. "
    "REGLA CRÍTICA: no inventes tecnologías, métricas, responsabilidades ni logros que no aparezcan "
    "en los datos proporcionados. Si un proyecto no tiene nota del usuario, describe SOLO lo que el "
    "README afirma literalmente, sin inferir el rol. No menciones frases como 'sin nota'. "
    "Si no hay información suficiente, dilo brevemente en vez de rellenar."
)

SYSTEM_CONSTRUCTOR = (
    "Genera una página HTML5 autocontenida (CSS inline, sin dependencias externas, sin JavaScript) "
    "para un portafolio profesional. Debe ser limpia, moderna, responsive y accesible. "
    "Incluye el nombre del usuario, el texto de perfil y una sección de proyectos si el texto los menciona. "
    "Si se proporciona un README de perfil con herramientas, agrega una sección de habilidades/herramientas "
    "que liste únicamente lo que aparece en él. "
    "Usa solo la información recibida; no agregues datos nuevos. "
    "Devuelve SOLO el HTML, sin explicaciones."
)


def _cliente() -> OpenAI:
    api_key = os.getenv("ABACUS_API_KEY")
    if not api_key:
        raise LLMError("Falta la variable de entorno ABACUS_API_KEY (revisa tu archivo .env).")
    return OpenAI(api_key=api_key, base_url=os.getenv("ABACUS_BASE_URL", DEFAULT_BASE_URL))


def _chat(system: str, user: str, temperature: float) -> str:
    try:
        resp = _cliente().chat.completions.create(
            model=os.getenv("ABACUS_MODEL", DEFAULT_MODEL),
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
        )
    except OpenAIError as exc:
        raise LLMError(f"Error al llamar al modelo: {exc}") from exc
    return (resp.choices[0].message.content or "").strip()


def redactar_perfil(usuario: str, repos_elegidos: list[dict], sobre_mi: str | None = None) -> str:
    """Agente Redactor: recibe solo los repos seleccionados y sus notas.

    `sobre_mi` es el README del perfil (escrito por la propia persona), opcional.
    """
    if not repos_elegidos:
        raise LLMError("No hay repositorios seleccionados.")

    bloques = []
    for r in repos_elegidos:
        bloques.append(
            f"Proyecto: {r['name']}\n"
            f"Lenguaje: {r.get('language') or 'no indicado'}\n"
            f"Descripción: {r.get('description') or 'no indicada'}\n"
            f"Nota del usuario sobre su rol: {r.get('nota_usuario') or '(sin nota)'}\n"
            f"README (recortado):\n{r.get('readme') or '(sin README)'}\n"
        )
    user = (
        f"Datos del usuario {usuario}:\n\n" + "\n---\n".join(bloques)
    )
    if sobre_mi:
        user += (
            "\n\nAdemás, este es el README del perfil que la propia persona escribió en GitHub "
            "(puede incluir su presentación y las herramientas que usa):\n" + sobre_mi
        )
    user += "\n\nEscribe un perfil profesional en español, en primera persona (máximo 250 palabras)."
    return _chat(SYSTEM_REDACTOR, user, temperature=0.4)


def construir_html(usuario: str, perfil: str, sobre_mi: str | None = None) -> str:
    """Agente Constructor: convierte el perfil aprobado en una página HTML."""
    if not perfil.strip():
        raise LLMError("El perfil está vacío.")
    user = f"Usuario: {usuario}\nPerfil aprobado:\n{perfil}"
    if sobre_mi:
        user += (
            "\n\nREADME del perfil de la persona (para la sección de herramientas/habilidades; "
            "usa solo lo que aparece aquí):\n" + sobre_mi
        )
    return _limpiar_html(_chat(SYSTEM_CONSTRUCTOR, user, temperature=0.3))


def _limpiar_html(texto: str) -> str:
    """Quita las cercas ```html ... ``` si el modelo las incluye."""
    m = re.search(r"```(?:html)?\s*(.*?)```", texto, flags=re.DOTALL | re.IGNORECASE)
    return (m.group(1) if m else texto).strip()
