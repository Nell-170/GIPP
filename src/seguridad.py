"""Defensas contra inyección de instrucciones (prompt injection).

Todo texto que viene de GitHub (README, descripciones, nombres) o de campos libres
se considera NO CONFIABLE: otra persona pudo escribirlo con la intención de manipular
al modelo. Este módulo lo limpia, lo marca como datos y detecta señales sospechosas.
Nada de aquí reemplaza la revisión humana: sirve para avisarle a la persona usuaria.
"""
import re

README_MAX_CHARS = 1500
NOTA_MAX_CHARS = 300
CAMPO_MAX_CHARS = 200

ETIQUETA_DATOS = "datos_no_confiables"

_INVISIBLES = dict.fromkeys(
    map(ord, "\u200b\u200c\u200d\u2060\ufeff\u00ad\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069"),
    None,
)
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_COMENTARIO_HTML = re.compile(r"<!--.*?(?:-->|\Z)", re.DOTALL)
_BLOQUE_ACTIVO = re.compile(r"<\s*(script|style|iframe|object|embed)\b.*?(?:<\s*/\s*\1\s*>|\Z)",
                            re.DOTALL | re.IGNORECASE)
_ETIQUETA_HTML = re.compile(r"</?[A-Za-z][^>]*>")
_NUESTRA_ETIQUETA = re.compile(rf"<\s*/?\s*{ETIQUETA_DATOS}[^>]*>?", re.IGNORECASE)
_LINEAS_VACIAS = re.compile(r"\n{3,}")

_PATRONES_SOSPECHOSOS = [
    ("pide ignorar las instrucciones",
     r"\b(ignor\w*|olvid\w*|desestim\w*|omit\w*|disregard|forget)\b.{0,40}\b(instruc\w*|indicaci\w*|reglas|"
     r"prompt\w*|instructions?|rules?)\b"),
    ("intenta cambiar el rol del modelo",
     r"\b(you are now|from now on|act as|eres ahora|a partir de ahora|act[uú]a como|compórtate como)\b"),
    ("menciona un prompt de sistema",
     r"\b(system prompt|prompt del sistema|developer message|mensaje del sistema)\b"),
    ("da instrucciones nuevas",
     r"\b(new instructions?|nuevas? instrucciones?|override|sobrescrib\w+)\b"),
    ("pide revelar información interna",
     r"\b(reveal|show|print|leak|revela\w*|muestra\w*|imprime|filtra)\b.{0,40}\b(prompt|instrucc\w*|"
     r"api[ _-]?key|clave|token|secret\w*|contraseña|password)\b"),
    ("pide insertar enlaces o contenido",
     r"\b(include|insert|add|append|incluye|inserta|agrega|añade)\b.{0,30}\b(link|url|enlace|script|"
     r"iframe|código|code)\b"),
    ("contiene código ejecutable",
     r"(<\s*script\b|javascript\s*:|\bon(error|load|click)\s*=)"),
]
_PATRONES_COMPILADOS = [(n, re.compile(p, re.IGNORECASE | re.DOTALL)) for n, p in _PATRONES_SOSPECHOSOS]

_URL = re.compile(r"https?://[^\s<>\")\]]+", re.IGNORECASE)
_CORREO = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")


def detectar_inyeccion(texto: str) -> list[str]:
    """Etiquetas de las señales sospechosas halladas en el texto original (sin limpiar)."""
    if not texto:
        return []
    crudo = texto.translate(_INVISIBLES)
    señales = [nombre for nombre, patron in _PATRONES_COMPILADOS if patron.search(crudo)]
    for comentario in _COMENTARIO_HTML.findall(texto):
        if any(p.search(comentario) for _, p in _PATRONES_COMPILADOS):
            señales.append("esconde instrucciones en un comentario HTML")
            break
    return list(dict.fromkeys(señales))


def sanitizar(texto: str | None, max_chars: int) -> str:
    """Quita lo invisible o ejecutable y recorta. Se limpia primero y se recorta después,
    para que el contenido oculto no consuma el espacio disponible."""
    if not texto:
        return ""
    t = texto.translate(_INVISIBLES)
    t = _CONTROL.sub("", t)
    t = _COMENTARIO_HTML.sub("", t)
    t = _BLOQUE_ACTIVO.sub("", t)
    t = _NUESTRA_ETIQUETA.sub("", t)
    t = _ETIQUETA_HTML.sub("", t)
    t = _LINEAS_VACIAS.sub("\n\n", t).strip()
    return t[:max_chars]


def en_una_linea(texto: str | None, max_chars: int) -> str:
    """Para campos cortos (nombre, descripción): una sola línea, sin etiquetas."""
    return re.sub(r"\s+", " ", sanitizar(texto, max_chars * 3)).strip()[:max_chars]


def marcar_no_confiable(origen: str, texto: str) -> str:
    """Envuelve el texto ya sanitizado para que el modelo lo distinga de las instrucciones."""
    origen_seguro = re.sub(r"[^A-Za-z0-9_ .:/-]", "", origen)[:80]
    return f'<{ETIQUETA_DATOS} origen="{origen_seguro}">\n{texto}\n</{ETIQUETA_DATOS}>'


def enlaces_no_respaldados(generado: str, fuentes: list[str]) -> list[str]:
    """URLs y correos que aparecen en la salida del modelo pero en ninguna fuente.
    Un enlace nuevo es la señal típica de una inyección que busca redirigir a la persona lectora."""
    base = "\n".join(fuentes).lower()
    hallados = _URL.findall(generado) + _CORREO.findall(generado)
    sospechosos = []
    for h in hallados:
        limpio = h.rstrip(".,;:!?)").lower()
        if limpio not in base and limpio not in sospechosos:
            sospechosos.append(limpio)
    return sospechosos


def limpiar_visible(texto: str | None, max_chars: int) -> str:
    """Para texto que se muestra tal cual (ya se escapa al renderizar): solo quita lo invisible."""
    if not texto:
        return ""
    return _CONTROL.sub("", texto.translate(_INVISIBLES)).strip()[:max_chars]


def aparece_en(valor: str, texto: str) -> bool:
    """True si `valor` aparece como palabra completa (sin distinguir mayúsculas) en `texto`."""
    return re.search(rf"(?<!\w){re.escape(valor)}(?!\w)", texto, flags=re.IGNORECASE) is not None
