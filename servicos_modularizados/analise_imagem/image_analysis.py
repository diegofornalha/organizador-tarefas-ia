"""
Script para análise de imagem com IA.
"""

import os
import sys
import streamlit as st
from dotenv import load_dotenv

# Adicionar caminhos para importação
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SERVICES_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GERAL_DIR = os.path.join(SERVICES_DIR, "geral")

# Adicionar diretórios ao path
sys.path.insert(0, ROOT_DIR)
sys.path.insert(0, SERVICES_DIR)
sys.path.insert(0, GERAL_DIR)

# Agora importar os módulos diretamente
from geral.app_logger import add_log, log_success, log_error, get_logs, clear_logs

# Importar o componente reutilizável
from components import image_analysis_standalone

# Carregar variáveis de ambiente
load_dotenv()

# Executar a aplicação standalone
if __name__ == "__main__":
    image_analysis_standalone()
