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
2. **Repositorios:** Tu README de perfil se muestra interpretado (Markdown convertido a HTML seguro, sin scripts ni imágenes externas). marca los que quieres incluir y escribe, si quieres, una línea sobre tu rol en cada uno. Si no escribes nada, la IA solo describirá lo que dice el README. Si tu perfil tiene un README propio (el repositorio con tu nombre de usuario), puedes decidir si se incluye: ahí suelen estar tu presentación y las herramientas que usas, y el portafolio las lista tal cual, sin inventar nada. También puedes subir tu CV (PDF, DOCX, TXT o MD, hasta 5 MB): se lee en memoria, se trata como texto no confiable y el modelo lo usa como contexto para la experiencia, la educación y las tecnologías que declares.
3. **Revisión:** Si subiste el CV en PDF (hasta 2 MB), puedes ofrecerlo como botón "Descargar CV" en la sección de contacto: el PDF se incrusta en la página, así que el archivo HTML sigue siendo autónomo. lee el perfil generado, corrige lo que no sea cierto y aprueba. Aquí también eliges la plantilla y, si quieres, escribes tu contacto (correo y LinkedIn). La IA no ve ni modifica el contacto; se valida el formato y será público en la página.
4. **Portafolio:** descarga el archivo HTML o revisa la vista previa.

## Estructura

```
GIPP/
├── src/
│   ├── app.py                # Interfaz Streamlit
│   ├── github_extractor.py   # Lectura de repos y READMEs (API de GitHub)
│   ├── llm_agents.py         # Redactor y constructor de datos (Abacus.AI)
│   ├── portafolio.py         # Plantilla HTML fija y escapada
│   └── seguridad.py          # Defensas contra inyección de instrucciones
├── Makefile
├── requirements.txt
├── .env.example
└── README.md
```

## Seguridad

Los README y descripciones de GitHub son texto no confiable (pueden traer instrucciones dirigidas a la IA). Defensas:

- El texto se limpia (caracteres invisibles, comentarios y etiquetas HTML), se recorta y se entrega a la IA delimitado como datos, con una regla que prohíbe obedecerlo.
- La IA nunca escribe HTML: solo devuelve nombre, titular y habilidades en JSON. La página sale de una plantilla fija con todo escapado, sin recursos externos y con Content-Security-Policy. El único script es el del mapa lateral, escrito por nosotros, fijo y autorizado por hash (`script-src 'sha256-…'`): si cambia una sola letra, el navegador lo bloquea.
- Nombre y habilidades solo se aceptan si aparecen literalmente en tus textos. Los enlaces solo apuntan a tu GitHub.
- La interfaz muestra alertas si detecta instrucciones sospechosas o enlaces que no están en tus datos, y tú revisas el perfil antes de generar la página.

## Privacidad

- Solo se leen repositorios públicos, y solo de los repos que seleccionas.
- Todo se procesa en memoria: la aplicación no tiene base de datos ni guarda el contenido en servidores propios.
- Los textos se recortan antes de usarse: READMEs a 3000 caracteres (inicio y final, donde suelen ir los créditos), CV a 4000 y tu nota de rol a 300.

**Qué se envía a Abacus.AI.** Para redactar el perfil, el texto se envía a Abacus.AI, un servicio externo de IA. Se envía el nombre de usuario de GitHub, el nombre, lenguaje y descripción de los repos seleccionados, sus READMEs, tus notas de rol, los logins de colaboradores de cada repo, tu README de perfil y el texto de tu CV (estos dos últimos solo si decides incluirlos). El archivo del CV no se envía: solo el texto extraído. **Tu correo y tu LinkedIn nunca se envían a la IA**; los escribes tú y van directo a la página.

Según la documentación pública de Abacus.AI (consultada en noviembre de 2026), el contenido del cliente no se usa para entrenar modelos, sus proveedores de modelos tienen retención cero, los datos se procesan en Estados Unidos y se eliminan 30 días después de cancelar el servicio. Son declaraciones de ese proveedor, no una auditoría independiente.

La aplicación te lo avisa en el paso 1 y no te deja continuar hasta que aceptes. Nada se publica sin que revises y apruebes el texto.

## Modelos

El Redactor y el Constructor usan el modelo definido en `ABACUS_MODEL` (por defecto `gpt-4o`) a través de Abacus.AI. El Extractor no usa ningún modelo: solo consulta la API pública de GitHub. Al ejecutar la app, la consola muestra qué modelo se pide y cuál respondió en cada paso.

## Estado

Prototipo en desarrollo para el Entregable 1 del proyecto.

## Declaratoria de uso de IA

En este proyecto se utilizaron como asistentes (supervisados y constantemente evaluados) de desarrollo, depuración y documentación a los modelos Claude Sonnet 5.5, DeepSeek V4.1 Flash y chatpgt Astra (para debbuguear).
