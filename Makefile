
# GIPP - Generador Inteligente de Portafolios Profesionales
# Uso: make <objetivo>   (ver 'make help')
#
# No hace falta activar el venv: los comandos llaman directamente a su Python.

VENV   := .venv
PYTHON ?= python

ifeq ($(OS),Windows_NT)
  PY := $(VENV)/Scripts/python.exe
else
  PY := $(VENV)/bin/python
endif

.PHONY: help venv install env run clean

help:
	@echo Objetivos disponibles:
	@echo   make install   Crea el venv e instala requirements.txt
	@echo   make env       Crea .env a partir de .env.example si no existe
	@echo   make run       Inicia la aplicacion Streamlit
	@echo   make clean     Borra el venv y los caches de Python

# Crea el venv solo si aun no existe.
$(PY):
	$(PYTHON) -m venv $(VENV)

venv: $(PY)

# Marca de instalación: se reinstala solo si cambia requirements.txt.
$(VENV)/.installed: requirements.txt | $(PY)
	$(PY) -m pip install -r requirements.txt
	$(PYTHON) -c "open(r'$@', 'w').close()"

install: $(VENV)/.installed

env:
	@$(PYTHON) -c "import os, shutil; print('.env ya existe, no se modifica') if os.path.exists('.env') else (shutil.copy('.env.example', '.env'), print('.env creado: completa ABACUS_API_KEY'))"

run: install
	$(PY) -m streamlit run src/app.py

clean:
	$(PYTHON) -c "import shutil, pathlib; [shutil.rmtree(p, ignore_errors=True) for p in [pathlib.Path('.venv')] + list(pathlib.Path('.').rglob('__pycache__'))]"
