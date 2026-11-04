"""Agente Extractor: consulta la API pública de GitHub.

Solo lee metadatos de repositorios públicos. El README se pide únicamente
para los repos que la persona usuaria seleccionó, y se recorta antes de
usarse. Nada se guarda en disco.
"""
import os
import re

import requests

GITHUB_API = "https://api.github.com"
README_MAX_CHARS = 8000
TIMEOUT_SEGUNDOS = 15


class GitHubError(Exception):
    """Error controlado al consultar GitHub (usuario inexistente, límite, red)."""


def _headers(raw: bool = False) -> dict:
    accept = "application/vnd.github.raw" if raw else "application/vnd.github+json"
    headers = {"Accept": accept, "X-GitHub-Api-Version": "2022-11-28"}
    token = os.getenv("GITHUB_TOKEN", "").strip()  # opcional: 5000 req/h en vez de 60
    if token and token != "tu_token_de_github":
        headers["Authorization"] = f"Bearer {token}"
    return headers


def normalizar_usuario(entrada: str) -> str:
    """Acepta 'usuario', 'github.com/usuario' o 'https://github.com/usuario/'."""
    texto = (entrada or "").strip()
    texto = re.sub(r"^(https?://)?(www\.)?github\.com/", "", texto, flags=re.IGNORECASE)
    texto = texto.strip("/").split("/")[0].split("?")[0]
    # Usuarios de GitHub: letras, números y guiones, máximo 39 caracteres.
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]{0,38}", texto):
        raise ValueError("El nombre de usuario de GitHub no es válido.")
    return texto


def _get(url: str, raw: bool = False) -> requests.Response:
    try:
        resp = requests.get(url, headers=_headers(raw), timeout=TIMEOUT_SEGUNDOS)
    except requests.RequestException as exc:
        raise GitHubError(f"No se pudo conectar con GitHub: {exc}") from exc

    if resp.status_code == 404:
        raise GitHubError("Usuario no encontrado en GitHub.")
    if resp.status_code in (403, 429):
        raise GitHubError(
            "GitHub rechazó la petición (posible límite de peticiones). "
            "Configura GITHUB_TOKEN o espera un rato."
        )
    if resp.status_code != 200:
        raise GitHubError(f"GitHub respondió con código {resp.status_code}.")
    return resp


def _metadatos(r: dict, usuario: str) -> dict:
    """Metadatos de un repo de la API, con su dueño (el repo puede ser de otra persona)."""
    dueno = (r.get("owner") or {}).get("login") or usuario
    return {
        "name": r["name"],
        "owner": dueno,
        "language": r.get("language"),
        "description": r.get("description"),
        "url": r.get("html_url"),
        "updated_at": r.get("updated_at"),
    }


def listar_repos(usuario: str) -> list[dict]:
    """Repos propios y públicos (sin forks) más los ajenos donde la persona participó.

    Los propios salen de /users/{usuario}/repos; los ajenos, de la búsqueda de commits
    de la persona. Se devuelven solo metadatos; el README se pide después.
    """
    url = f"{GITHUB_API}/users/{usuario}/repos?per_page=100&sort=updated"
    repos = _get(url).json()
    vistos = {r["name"] for r in repos}
    propios = [_metadatos(r, usuario) for r in repos if not r.get("fork")]

    ajenos = []
    for repo in _repos_con_commits(usuario):
        nombre = repo.get("name")
        if not isinstance(nombre, str) or nombre in vistos:
            continue
        vistos.add(nombre)
        ajenos.append(_metadatos(repo, usuario))
    ajenos.sort(key=lambda r: r.get("updated_at") or "", reverse=True)
    return propios + ajenos


def _repos_con_commits(usuario: str) -> list[dict]:
    """Repos donde la persona tiene commits, incluidos los de otras personas.

    Usa la búsqueda de commits (requiere GITHUB_TOKEN). Si no hay token o falla,
    devuelve una lista vacía: el flujo sigue solo con los repos propios.
    """
    if not os.getenv("GITHUB_TOKEN", "").strip():
        return []
    encontrados: dict[str, dict] = {}
    for pagina in range(1, 4):  # hasta 300 commits recientes
        url = (
            f"{GITHUB_API}/search/commits?q=author:{usuario}&sort=committer-date&order=desc"
            f"&per_page=100&page={pagina}"
        )
        try:
            resp = _get(url)
        except GitHubError:
            break
        try:
            datos = resp.json()
        except ValueError:
            break
        items = datos.get("items") if isinstance(datos, dict) else None
        if not isinstance(items, list) or not items:
            break
        for item in items:
            repo = item.get("repository") if isinstance(item, dict) else None
            if isinstance(repo, dict) and isinstance(repo.get("full_name"), str):
                encontrados[repo["full_name"]] = repo
        if len(items) < 100:
            break
    return list(encontrados.values())


def obtener_readme(dueno: str, nombre_repo: str) -> str:
    """README recortado a README_MAX_CHARS. Cadena vacía si no hay o falla."""
    try:
        resp = _get(f"{GITHUB_API}/repos/{dueno}/{nombre_repo}/readme", raw=True)
    except GitHubError:
        return ""  # el README es opcional; el flujo sigue sin él
    return resp.text[:README_MAX_CHARS]


def obtener_colaboradores(dueno: str, nombre_repo: str) -> list[str] | None:
    """Logins de quienes contribuyeron al repo según GitHub. None si no se pudo consultar."""
    try:
        datos = _get(f"{GITHUB_API}/repos/{dueno}/{nombre_repo}/contributors?per_page=30").json()
    except (GitHubError, ValueError):
        return None
    if not isinstance(datos, list):
        return None
    return [c["login"] for c in datos if isinstance(c, dict) and isinstance(c.get("login"), str)]
