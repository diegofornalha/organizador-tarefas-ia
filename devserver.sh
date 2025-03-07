#!/bin/sh
source .venv/bin/activate 2>/dev/null || true  # Tenta ativar o ambiente virtual, ignora erros
python -m streamlit run app.py 