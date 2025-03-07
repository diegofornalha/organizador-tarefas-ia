import streamlit as st
import os
import logging
from dotenv import load_dotenv

# Carregar variáveis de ambiente do .env
load_dotenv()

from home import show_home_page, init_session_state

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuração da página
st.set_page_config(
    page_title="Organizador de Tarefas com IA",
    page_icon="📋",
    layout="wide"
)

# Inicializar estado da sessão (inclui serviços)
init_session_state()

# Função para adicionar logs (melhorada com debug)
def add_log(message):
    if not 'logs' in st.session_state:
        st.session_state.logs = []
    
    # Adicionar timestamp
    from datetime import datetime
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    # Adicionar log com timestamp
    log_entry = f"{timestamp} - {message}"
    st.session_state.logs.append(log_entry)
    
    # Log também para o console
    logger.info(message)
    
    # Limitar logs para os 100 mais recentes
    if len(st.session_state.logs) > 100:
        st.session_state.logs = st.session_state.logs[-100:]

# Adicionar log inicial
add_log("Página carregada")

# Mostrar a página principal unificada
show_home_page()

# Rodapé
st.markdown("---")
st.caption("Organizador de Tarefas com IA © 2024 - Desenvolvido com Streamlit e Python") 