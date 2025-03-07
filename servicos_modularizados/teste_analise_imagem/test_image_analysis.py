"""
Script isolado para testar o serviço de análise de imagem.
"""
import streamlit as st
import sys
import os
from dotenv import load_dotenv

# Adicionar diretórios ao path para importações
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Agora importamos os módulos necessários
from app_logger import add_log, log_success, log_error, get_logs, clear_logs
from image_analysis_service import ImageAnalysisService

# Carregar variáveis de ambiente
load_dotenv()

# Configurar página
st.set_page_config(
    page_title="Análise de Imagem",
    page_icon="🔍",
    layout="wide"
)

# Inicializar serviço de análise de imagem
if 'image_analysis_service' not in st.session_state:
    try:
        st.session_state.image_analysis_service = ImageAnalysisService(
            debug_mode=True
        )
        log_success("Serviço de análise de imagem inicializado")
    except Exception as e:
        log_error(f"Erro ao inicializar serviço: {str(e)}")

# Título da página
st.title("🔍 Análise de Imagem")
st.write("Ferramenta isolada para teste do serviço de análise de imagem.")

# Exibir logs
with st.expander("Logs do Sistema", expanded=False):
    cols = st.columns([4, 1])
    with cols[1]:
        if st.button("Limpar Logs"):
            clear_logs()
            st.success("Logs limpos")
            st.rerun()

    logs = get_logs(max_count=20)
    if logs:
        for log in logs:
            st.text(log)
    else:
        st.info("Nenhum log registrado ainda.")

# Interface principal
st.header("Teste de Análise de Imagem")

# Upload de imagem
uploaded_file = st.file_uploader(
    "Escolha uma imagem",
    type=["jpg", "jpeg", "png"],
    key="image_analysis_uploader"
)

if uploaded_file is not None:
    # Mostrar imagem
    st.image(uploaded_file, caption="Imagem carregada", width=300)

    # Opções de análise - APENAS as duas solicitadas
    options = st.radio(
        "Escolha o tipo de análise:",
        ["Análise simples", "Geração de planejamento"]
    )

    # Descrição adicional se for planejamento
    description = ""
    if options == "Geração de planejamento":
        description = st.text_area(
            "Descrição adicional para o planejamento:",
            placeholder="Ex: Planejar uma viagem para este destino"
        )

    if st.button("Analisar Imagem"):
        add_log(f"Iniciando análise de imagem: {options}")

        with st.spinner("Processando imagem..."):
            try:
                # Obter serviço
                image_service = st.session_state.image_analysis_service

                if options == "Análise simples":
                    # Análise simples
                    prompt = "Descreva esta imagem brevemente."
                    resultado = image_service.analyze_image(
                        uploaded_file,
                        prompt=prompt
                    )
                    log_success("Análise de imagem concluída com sucesso")

                    # Exibir resultado
                    st.subheader("Resultado da Análise")
                    st.write(resultado)

                else:
                    # Geração de planejamento
                    resultado = image_service.generate_planning_from_image(
                        uploaded_file,
                        description=description
                    )
                    log_success("Plano gerado com sucesso")

                    # Exibir resultado
                    st.subheader("Plano Gerado")
                    st.write(resultado)

            except Exception as e:
                log_error(f"Erro na análise: {str(e)}")
                st.error(f"Ocorreu um erro durante a análise: {str(e)}")

# Informações sobre o isolamento
with st.expander("Sobre esta ferramenta"):
    st.write("""
    Esta é uma versão isolada do serviço de análise de imagem.
    Ela contém apenas as funcionalidades essenciais:

    1. **Análise simples**: Descrição breve da imagem
    2. **Geração de planejamento**: Criação de um plano baseado na imagem

    Esta ferramenta funciona de forma independente do restante da aplicação.
    """)
