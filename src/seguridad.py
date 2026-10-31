"""Defensas contra inyección de instrucciones (prompt injection).

Todo texto que viene de GitHub (README, descripciones, nombres) o de campos libres
se considera NO CONFIABLE: otra persona pudo escribirlo con la intención de manipular
al modelo. Este módulo lo limpia, lo marca como datos y detecta señales sospechosas.
Nada de aquí reemplaza la revisión humana: sirve para avisarle a la persona usuaria.
"""
import re
from html import escape as html_escape

README_MAX_CHARS = 3000
README_DESCARGA_MAX = 8000
CV_MAX_CHARS = 4000
CV_ARCHIVO_MAX_BYTES = 5 * 1024 * 1024
CV_INCRUSTADO_MAX_BYTES = 2 * 1024 * 1024
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


def recortar_extremos(texto: str, max_chars: int) -> str:
    """Si el texto es largo, conserva el inicio y el final (los créditos suelen ir al final)."""
    if len(texto) <= max_chars:
        return texto
    inicio = int(max_chars * 0.7)
    return texto[:inicio].rstrip() + "\n[...]\n" + texto[-(max_chars - inicio):].lstrip()


_SEÑAL_EQUIPO = re.compile(
    r"cr[eé]ditos|autores|integrantes|equipo|colaborador|desarrollado por|elaborado por|"
    r"grupo|grupal|compa[ñn]er|credits|authors|contributors|team|members|developed by|"
    r"built by|\b[BC]\d{5}\b",
    re.IGNORECASE,
)


def señales_equipo(texto: str | None) -> bool:
    """True si el texto sugiere que el trabajo fue de más de una persona."""
    return bool(texto and _SEÑAL_EQUIPO.search(texto))


_AUTORIA_UNICA = re.compile(
    r"\b(yo solo|yo sola|por mi cuenta|completamente solo|completamente sola|"
    r"[uú]nicamente yo|(?:lo|la) (?:hice|desarroll[eé]|constru[ií]) (?:yo )?(?:solo|sola|todo|toda)|"
    r"desarroll[eé] (?:todo|toda|por completo|de principio a fin|de forma individual)|"
    r"(?:constru[ií]|cre[eé]|dise[ñn][eé]|implement[eé]) (?:todo|toda|por completo|desde cero yo))",
    re.IGNORECASE,
)


def afirma_autoria_unica(texto: str | None) -> bool:
    return bool(texto and _AUTORIA_UNICA.search(texto))


_CORREO = re.compile(r"[A-Za-z0-9._%+-]{1,64}@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)*\.[A-Za-z]{2,24}")
_LINKEDIN = re.compile(
    r"(?:https?://)?(?:[a-z]{2,3}\.|www\.)?linkedin\.com/in/([A-Za-z0-9%_-]{3,100})/?", re.IGNORECASE
)


def validar_contacto(correo: str | None, linkedin: str | None) -> tuple[dict[str, str], list[str]]:
    """Valida los datos de contacto que escribe la persona. Devuelve (datos válidos, errores).

    Solo se aceptan un correo con forma estándar y un perfil de linkedin.com/in/...;
    el enlace se reconstruye a partir de datos validados, nunca se copia tal cual.
    """
    datos: dict[str, str] = {}
    errores: list[str] = []
    correo = (correo or "").strip()
    if correo:
        if len(correo) <= 120 and _CORREO.fullmatch(correo):
            datos["correo"] = correo
        else:
            errores.append("El correo no tiene un formato válido (ejemplo: nombre@dominio.com).")
    linkedin = (linkedin or "").strip()
    if linkedin:
        m = _LINKEDIN.fullmatch(linkedin)
        if m:
            datos["linkedin"] = "https://www.linkedin.com/in/" + m.group(1)
        else:
            errores.append("El enlace de LinkedIn debe ser de la forma https://www.linkedin.com/in/tu-usuario.")
    return datos, errores


def texto_de_cv(nombre: str, contenido: bytes) -> str:
    """Extrae el texto de un CV en PDF, DOCX o TXT. Lanza ValueError con un mensaje para la persona."""
    nombre = (nombre or "").lower()
    if len(contenido) > CV_ARCHIVO_MAX_BYTES:
        raise ValueError("El archivo supera los 5 MB. Sube una versión más liviana.")
    if nombre.endswith(".pdf"):
        import pymupdf

        try:
            with pymupdf.open(stream=contenido, filetype="pdf") as documento:
                if documento.needs_pass:
                    raise ValueError("El PDF está protegido con contraseña. Súbelo sin contraseña.")
                texto = "\n".join(pagina.get_text() for pagina in documento)
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError("No se pudo leer el PDF. Prueba con otro archivo.") from exc
    elif nombre.endswith(".docx"):
        import io

        try:
            import docx

            documento = docx.Document(io.BytesIO(contenido))
        except Exception as exc:
            raise ValueError("No se pudo leer el DOCX. Prueba con otro archivo.") from exc
        partes = [p.text for p in documento.paragraphs]
        for tabla in documento.tables:
            for fila in tabla.rows:
                partes.append(" | ".join(celda.text for celda in fila.cells))
        texto = "\n".join(partes)
    elif nombre.endswith((".txt", ".md")):
        texto = contenido.decode("utf-8", errors="replace")
    elif nombre.endswith(".doc"):
        raise ValueError("El formato .doc antiguo no se puede leer. Guárdalo como PDF o DOCX.")
    else:
        raise ValueError("Formato no admitido. Sube un PDF, DOCX, TXT o MD.")
    if not sanitizar(texto, 1).strip():
        raise ValueError("El archivo no tiene texto legible (¿es un PDF escaneado como imagen?).")
    return texto


_MD_IMAGEN = re.compile(r"!\[([^\]]*)\]\(([^)\s]*)(?:\s+\"[^\"]*\")?\)")
_MD_ENLACE = re.compile(r"\[([^\]]+)\]\(([^)\s]*)(?:\s+\"[^\"]*\")?\)")
_MD_URL_SUELTA = re.compile(r"""(?<![\w"'=])(https?://[^\s<>()"']+)""")


def _md_en_linea(texto: str) -> str:
    """Formato en línea de Markdown a HTML, escapando todo el texto."""
    t = html_escape(texto)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"__([^_]+)__", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![*\w])\*([^*\s][^*]*)\*(?![*\w])", r"<em>\1</em>", t)
    t = re.sub(r"~~([^~]+)~~", r"<del>\1</del>", t)
    return t


def _md_enlace(url: str, etiqueta: str) -> str:
    """Solo enlaces http(s) o correo; cualquier otro esquema se deja como texto."""
    url = url.strip()
    if re.fullmatch(r"""https?://[^\s<>"']+""", url):
        return f'<a href="{html_escape(url)}" target="_blank" rel="noopener noreferrer">{etiqueta}</a>'
    if re.fullmatch(_CORREO, url):
        return f'<a href="mailto:{html_escape(url)}">{etiqueta}</a>'
    return etiqueta


def markdown_a_html(texto: str | None) -> str:
    """Convierte un README de Markdown a HTML seguro: sin scripts, sin imágenes remotas,
    sin HTML del original y sin enlaces que no sean http(s) o correo."""
    if not texto:
        return ""
    lineas = sanitizar(texto, 20000).splitlines()
    salida: list[str] = []
    lista: list[str] | None = None
    parrafo: list[str] = []
    en_codigo = False
    codigo: list[str] = []

    def cerrar_parrafo() -> None:
        if parrafo:
            salida.append("<p>" + _md_en_linea(" ".join(parrafo)) + "</p>")
            parrafo.clear()

    def cerrar_lista() -> None:
        nonlocal lista
        if lista is not None:
            salida.append(f"<{lista}>" + "".join(f"<li>{x}</li>" for x in lista_items) + f"</{lista}>")
            lista = None
            lista_items.clear()

    lista_items: list[str] = []
    for linea in lineas:
        if linea.strip().startswith("```"):
            cerrar_parrafo()
            cerrar_lista()
            if en_codigo:
                salida.append("<pre><code>" + html_escape("\n".join(codigo)) + "</code></pre>")
                codigo.clear()
            en_codigo = not en_codigo
            continue
        if en_codigo:
            codigo.append(linea)
            continue
        if not linea.strip():
            cerrar_parrafo()
            cerrar_lista()
            continue
        if re.fullmatch(r"\s{0,3}([-*_])(\s*\1){2,}\s*", linea):
            cerrar_parrafo()
            cerrar_lista()
            salida.append("<hr>")
            continue
        titulo = re.match(r"\s{0,3}(#{1,6})\s+(.*)", linea)
        if titulo:
            cerrar_parrafo()
            cerrar_lista()
            nivel = len(titulo.group(1))
            salida.append(f"<h{nivel}>{_md_en_linea(titulo.group(2).strip())}</h{nivel}>")
            continue
        vineta = re.match(r"\s{0,3}[-*+]\s+(.*)", linea)
        numerada = re.match(r"\s{0,3}\d+[.)]\s+(.*)", linea)
        if vineta or numerada:
            cerrar_parrafo()
            tipo = "ol" if numerada else "ul"
            if lista != tipo:
                cerrar_lista()
                lista = tipo
            lista_items.append(_md_en_linea((vineta or numerada).group(1)))
            continue
        cita = re.match(r"\s{0,3}>\s?(.*)", linea)
        if cita:
            cerrar_parrafo()
            cerrar_lista()
            salida.append("<blockquote>" + _md_en_linea(cita.group(1)) + "</blockquote>")
            continue
        parrafo.append(linea.strip())
    if en_codigo and codigo:
        salida.append("<pre><code>" + html_escape("\n".join(codigo)) + "</code></pre>")
    cerrar_parrafo()
    cerrar_lista()
    html = "\n".join(salida)
    # imágenes: solo se muestra el texto alternativo (no se cargan recursos externos)
    html = _MD_IMAGEN.sub(lambda m: f'<span class="imagen">{_md_en_linea(m.group(1))}</span>', html)
    html = _MD_ENLACE.sub(
        lambda m: _md_enlace(m.group(2), _md_en_linea(m.group(1)))
        if "(" not in m.group(2) and ")" not in m.group(2)
        else m.group(0),
        html,
    )
    html = _MD_URL_SUELTA.sub(lambda m: _md_enlace(m.group(1), html_escape(m.group(1))), html)
    return html


def cv_incrustable(nombre: str, contenido: bytes | None) -> str | None:
    """Devuelve el tipo MIME si el CV se puede incrustar en la página (PDF pequeño), o None."""
    if not contenido or not (nombre or "").lower().endswith(".pdf"):
        return None
    if len(contenido) > CV_INCRUSTADO_MAX_BYTES or not contenido.startswith(b"%PDF-"):
        return None
    return "application/pdf"


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
