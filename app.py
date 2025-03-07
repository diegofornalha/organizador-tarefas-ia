import streamlit as st
import logging
from dotenv import load_dotenv

# Carregar variáveis de ambiente do .env
load_dotenv()

# Importar serviços e módulos
from home import show_home_page, init_session_state
from servicos_modularizados import (
    add_log, log_success, log_error,
    ImageAnalysisService
)
from servicos_modularizados.sidebar_components import (
    show_service_selector
)

# Configurar logging básico
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

# Barra lateral para configurações
with st.sidebar:
    st.title("Configurações")

    # Mostrar seletor de serviço
    use_modular = show_service_selector()

    # Opção para depuração
    debug_mode = st.checkbox(
        "Modo de debug",
        value=st.session_state.get('debug_mode', False)
    )
    if debug_mode != st.session_state.get('debug_mode', False):
        st.session_state.debug_mode = debug_mode
        log_success(f"Modo de debug {' ativado' if debug_mode else ' desativado'}")

# Inicializar serviço de análise de imagem se necessário
if 'image_analysis_service' not in st.session_state and st.session_state.get('use_modular_service', True):
    try:
        st.session_state.image_analysis_service = ImageAnalysisService(
            debug_mode=st.session_state.get('debug_mode', False)
        )
        log_success("Serviço de análise de imagem inicializado")
    except Exception as e:
        log_error(f"Erro ao inicializar serviço de análise de imagem: {str(e)}")

# Adicionar log inicial
add_log("Página carregada")

# Mostrar a página principal unificada
show_home_page()

# Rodapé
st.markdown("---")
st.caption(
    "Organizador de Tarefas com IA © 2024 - Desenvolvido com Streamlit e Python"
)
