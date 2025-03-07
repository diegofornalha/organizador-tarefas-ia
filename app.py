import streamlit as st
import os
import logging

from task_service import TaskService
from firebase_service import FirebaseService
from gemini_service import GeminiService
from home import show_home_page

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuração da página
st.set_page_config(
    page_title="Organizador de Tarefas com Gemini",
    page_icon="📋",
    layout="wide"
)

# Inicialização dos serviços e configurações
@st.cache_resource
def initialize_services():
    # Inicializar serviço Gemini com a chave padrão
    gemini_service = GeminiService()
    gemini_api_key = os.environ.get("GEMINI_API_KEY", "AIzaSyAgdDdQ-IUxDvrbZM96dtZ-p26emIOf9Mw")
    gemini_service.save_config(gemini_api_key)
    
    # Inicializar Firebase (vai usar modo offline se falhar)
    firebase_service = FirebaseService()
    if getattr(firebase_service, 'is_offline_mode', True):
        logger.info("Firebase em modo offline. Dados armazenados localmente.")
    
    # Instância do serviço de tarefas (agora funciona com Firebase offline)
    task_service = TaskService()
    
    return {
        "gemini": gemini_service,
        "firebase": firebase_service,
        "task": task_service
    }

# Inicializar serviços com tratamento de erro
try:
    services = initialize_services()
except Exception as e:
    logger.error(f"Erro ao inicializar serviços: {str(e)}")
    # Criar objeto de serviços vazio para evitar erros
    services = {
        "gemini": GeminiService(),
        "task": None,
        "firebase": None
    }

# Barra lateral para configurações e debug
with st.sidebar:
    st.header("Configurações")
    
    # Configuração do Gemini
    with st.expander("API Gemini", expanded=True):
        current_api_key = services["gemini"].api_key if hasattr(services["gemini"], "api_key") else ""
        masked_key = "••••••••" + current_api_key[-4:] if current_api_key else ""
        
        st.write(f"API Key atual: {masked_key}")
        
        # Link para gerar chave API
        st.markdown("""
        <div style="margin: 10px 0; padding: 10px; border-radius: 5px; background-color: rgba(70, 130, 180, 0.1); border: 1px solid rgba(70, 130, 180, 0.3);">
            <a href="https://aistudio.google.com/apikey" target="_blank">🔑 Gerar API Key</a>
        </div>
        """, unsafe_allow_html=True)
        
        gemini_key = st.text_input(
            "Nova Chave API Gemini",
            type="password",
            placeholder="Insira nova chave API se necessário"
        )
        
        model = st.selectbox(
            "Modelo", 
            ["gemini-pro", "gemini-pro-vision", "gemini-2.0-flash"],
            index=2
        )
        
        if gemini_key and st.button("Atualizar API Key"):
            try:
                services["gemini"].save_config(gemini_key, model)
                # Atualizar a variável de ambiente também
                os.environ["GEMINI_API_KEY"] = gemini_key
                st.success("✅ Chave da API atualizada com sucesso!")
                logger.info("API Key do Gemini atualizada")
            except Exception as e:
                st.error(f"Erro ao atualizar a chave: {str(e)}")
                logger.error(f"Erro ao atualizar API Key: {str(e)}")
    
    # Debug e Status
    with st.expander("Status do Sistema", expanded=False):
        # Status do Firebase
        firebase_status = "Offline (armazenamento local)" 
        if services.get("firebase") and not getattr(services["firebase"], 'is_offline_mode', True):
            firebase_status = "Online (conectado ao Firestore)"
        
        st.subheader("Firebase")
        st.info(firebase_status)
        
        # Status do Gemini
        st.subheader("Gemini API")
        if hasattr(services["gemini"], "api_key") and services["gemini"].api_key:
            st.success("Conectado")
        else:
            st.warning("Chave API não configurada")
        
        # Log simplificado
        if "log_messages" not in st.session_state:
            st.session_state.log_messages = ["Sistema iniciado"]
        
        st.subheader("Log de Eventos")
        log_container = st.container(height=200)
        with log_container:
            for msg in st.session_state.log_messages:
                st.text(msg)
        
        if st.button("Limpar Log"):
            st.session_state.log_messages = ["Log limpo"]
            st.rerun()

# Função para adicionar mensagem ao log
def add_log(message):
    if "log_messages" in st.session_state:
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        st.session_state.log_messages.append(f"[{timestamp}] {message}")
        # Limitar o tamanho do log
        if len(st.session_state.log_messages) > 100:
            st.session_state.log_messages = st.session_state.log_messages[-100:]

# Adicionar log inicial
add_log("Página carregada")

# Mostrar a página principal unificada
show_home_page()

# Rodapé
st.markdown("---")
st.caption("Organizador de Tarefas com Gemini © 2024 - Desenvolvido com Streamlit e Python") 