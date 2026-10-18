"""Agente Extractor: consulta la API pública de GitHub.

Solo lee metadatos de repositorios públicos. El README se pide únicamente
para los repos que la persona usuaria seleccionó, y se recorta antes de
usarse. Nada se guarda en disco.
"""
import os
import re

import requests

GITHUB_API = "https://api.github.com"
README_MAX_CHARS = 1500
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


def listar_repos(usuario: str) -> list[dict]:
    """Devuelve los repos propios y públicos (sin forks), solo metadatos."""
    url = f"{GITHUB_API}/users/{usuario}/repos?per_page=100&sort=updated"
    repos = _get(url).json()
    return [
        {
            "name": r["name"],
            "language": r.get("language"),
            "description": r.get("description"),
            "url": r.get("html_url"),
            "updated_at": r.get("updated_at"),
        }
        for r in repos
        if not r.get("fork")  # los forks no son trabajo propio
    ]


def obtener_readme(usuario: str, nombre_repo: str) -> str:
    """README recortado a README_MAX_CHARS. Cadena vacía si no hay o falla."""
    try:
        resp = _get(f"{GITHUB_API}/repos/{usuario}/{nombre_repo}/readme", raw=True)
    except GitHubError:
        return ""  # el README es opcional; el flujo sigue sin él
    return resp.text[:README_MAX_CHARS]
