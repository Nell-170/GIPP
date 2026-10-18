# GIPP: Generador Inteligente de Portafolios Profesionales

Herramienta que lee tus repositorios públicos de GitHub, te deja elegir cuáles incluir y el rol que tuviste en cada uno, redacta un perfil profesional con IA y genera una página HTML de portafolio. **Tú revisas y editas el texto antes de generar la página.** La IA no puede inventar tecnologías ni logros que no aparezcan en tus datos.

Proyecto E del curso CI-0133 Computación y Sociedad (UCR).

## Requisitos

- Python 3.10 o superior
- Una clave de API de Abacus.AI
- (Opcional, recomendado) Un token de GitHub para tener más peticiones por hora

## Instalación y uso

### Opción A: con Makefile (recomendada)

Requiere tener `make` instalado. Los comandos usan el venv del proyecto directamente, así que no hace falta activarlo.

```
make env        # crea .env a partir de .env.example
make install    # crea .venv e instala las dependencias
make run        # inicia la aplicación
```

Otros objetivos: `make help` muestra la lista y `make clean` borra `.venv` y los caches de Python.

### Opción B: sin Makefile

```
pip install -r requirements.txt
copy .env.example .env
streamlit run src/app.py
```

- `pip install -r requirements.txt` instala las librerías del proyecto (`streamlit`, `openai`, `requests`, `python-dotenv`).
- `copy .env.example .env` crea tu archivo de configuración. En Git Bash o macOS/Linux usa `cp .env.example .env`.
- `streamlit run src/app.py` inicia la aplicación y abre el servidor local, normalmente en `http://localhost:8501`. Para detenerla, presiona `Ctrl+C`.

Si prefieres un entorno aislado sin Makefile:

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Configuración

Edita `.env` y completa:

| Variable | Obligatoria | Descripción |
|---|---|---|
| `ABACUS_API_KEY` | Sí | Clave de Abacus.AI |
| `GITHUB_TOKEN` | No | Token de GitHub: sube el límite de 60 a 5000 peticiones por hora |
| `ABACUS_BASE_URL` | No | Endpoint compatible con OpenAI |
| `ABACUS_MODEL` | No | Modelo a usar |

**No subas `.env` a GitHub.** Ya está incluido en `.gitignore`. No pegues tus claves en issues, capturas ni en el chat.

La primera vez que ejecutes Streamlit puede pedirte un correo en la consola. Es opcional: puedes dejarlo vacío y presionar Enter.

## Uso de la aplicación

1. **Usuario de GitHub:** escribe tu usuario o la URL de tu perfil.
2. **Repositorios:** marca los que quieres incluir y escribe, si quieres, una línea sobre tu rol en cada uno. Si no escribes nada, la IA solo describirá lo que dice el README. Si tu perfil tiene un README propio (el repositorio con tu nombre de usuario), puedes decidir si se incluye: ahí suelen estar tu presentación y las herramientas que usas, y el portafolio las lista tal cual, sin inventar nada.
3. **Revisión:** lee el perfil generado, corrige lo que no sea cierto y aprueba.
4. **Portafolio:** descarga el archivo HTML o revisa la vista previa.

## Estructura

```
GIPP/
├── src/
│   ├── app.py                # Interfaz Streamlit
│   ├── github_extractor.py   # Lectura de repos y READMEs (API de GitHub)
│   └── llm_agents.py         # Redactor y constructor del HTML (Abacus.AI)
├── Makefile
├── requirements.txt
├── .env.example
└── README.md
```

## Privacidad

- Solo se leen repositorios públicos.
- Los READMEs se procesan en memoria, se recortan a 1500 caracteres y no se guardan.
- Solo se pide el README de los repos que seleccionas.

## Estado

Prototipo en desarrollo para el Entregable 1 del proyecto.
