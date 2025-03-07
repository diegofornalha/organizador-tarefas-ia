"""
Módulo para gerenciamento de logs da aplicação.
Fornece funcionalidades para registrar logs no estado da sessão do Streamlit e no console.
"""
import streamlit as st
import logging
from datetime import datetime

# Configurar logging básico
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_log(message):
    """
    Adiciona uma entrada de log ao estado da sessão e também ao logger do sistema.

    Args:
        message (str): Mensagem para registrar no log
    """
    if 'logs' not in st.session_state:
        st.session_state.logs = []

    # Adicionar timestamp
    timestamp = datetime.now().strftime("%H:%M:%S")

    # Adicionar log com timestamp
    log_entry = f"{timestamp} - {message}"
    st.session_state.logs.append(log_entry)

    # Log também para o console
    logger.info(message)

    # Limitar logs para os 100 mais recentes
    if len(st.session_state.logs) > 100:
        st.session_state.logs = st.session_state.logs[-100:]

def get_logs(max_count=10):
    """
    Retorna os logs mais recentes do estado da sessão.

    Args:
        max_count (int): Número máximo de logs a retornar

    Returns:
        list: Lista com as entradas de log mais recentes
    """
    if 'logs' not in st.session_state:
        return []

    # Retornar os logs mais recentes
    return st.session_state.logs[-max_count:]

def clear_logs():
    """
    Limpa todos os logs do estado da sessão.
    """
    if 'logs' in st.session_state:
        st.session_state.logs = []
        logger.info("Logs limpos")

def log_error(message):
    """
    Registra uma mensagem de erro no log e exibe um erro no Streamlit.

    Args:
        message (str): Mensagem de erro
    """
    add_log(f"ERRO: {message}")
    logger.error(message)
    st.error(message)

def log_warning(message):
    """
    Registra uma mensagem de aviso no log e exibe um aviso no Streamlit.

    Args:
        message (str): Mensagem de aviso
    """
    add_log(f"AVISO: {message}")
    logger.warning(message)
    st.warning(message)

def log_success(message):
    """
    Registra uma mensagem de sucesso no log e exibe uma mensagem de sucesso no Streamlit.

    Args:
        message (str): Mensagem de sucesso
    """
    add_log(message)
    logger.info(message)
    st.success(message)

def log_debug(message, show_ui=False):
    """
    Registra uma mensagem de debug no log e opcionalmente exibe no Streamlit.

    Args:
        message (str): Mensagem de debug
        show_ui (bool): Se deve exibir a mensagem na interface do Streamlit
    """
    if 'debug_mode' in st.session_state and st.session_state.debug_mode:
        add_log(f"DEBUG: {message}")
        logger.debug(message)

        if show_ui:
            st.info(f"🔍 DEBUG: {message}")
