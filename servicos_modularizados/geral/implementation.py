"""
Script para implementação do serviço de análise de imagem.
"""

import streamlit as st
import os
import sys
from dotenv import load_dotenv

# Configurar página - DEVE SER O PRIMEIRO COMANDO STREAMLIT!
st.set_page_config(page_title="Análise de Imagem", page_icon="🔍", layout="wide")

# Importar módulos - usando importações diretas
from app_logger import add_log, log_success, log_error, get_logs, clear_logs
from image_analysis_service import ImageAnalysisService

# Tentar importar os componentes reutilizáveis
try:
    # Adicionar caminho para o módulo analise_imagem
    analise_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "analise_imagem"
    )
    if analise_path not in sys.path:
        sys.path.append(analise_path)

    # Importar o componente
    from analise_imagem.components import image_analysis_ui

    # Flag para indicar que o componente foi importado com sucesso
    has_components = True
    log_success("Componente de análise de imagem importado com sucesso")
except ImportError as e:
    has_components = False
    log_error(f"Não foi possível importar componente: {str(e)}")

# Carregar variáveis de ambiente
load_dotenv()

# Inicializar estado da sessão
if "last_plan" not in st.session_state:
    st.session_state.last_plan = None

# Inicializar serviço de análise de imagem
if "image_analysis_service" not in st.session_state:
    try:
        st.session_state.image_analysis_service = ImageAnalysisService(debug_mode=True)
        st.session_state.debug_mode = True
        log_success("Serviço de análise de imagem inicializado")
    except Exception as e:
        log_error(f"Erro ao inicializar serviço de análise de imagem: {str(e)}")

# Título da página
st.title("🔍 Análise de Imagem")
st.write("Esta página permite testar o serviço de análise de imagem.")

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

# Interface principal - Análise de Imagem
st.header("Teste de Análise de Imagem")

# Verificar se podemos usar o componente reutilizável
if has_components:
    try:
        # Usar o componente diretamente
        uploaded_file, result = image_analysis_ui()

        # Se tiver um resultado, armazenar
        if result and uploaded_file:
            st.session_state.last_result = result
    except Exception as e:
        log_error(f"Erro ao usar componente reutilizável: {str(e)}")
        # Se falhar, voltamos para a implementação local
        has_components = False

# Se não conseguiu usar o componente, usar a implementação local
if not has_components:
    # Upload de imagem
    uploaded_file = st.file_uploader(
        "Escolha uma imagem",
        type=["jpg", "jpeg", "png"],
        key="image_analysis_uploader",
    )

    if uploaded_file is not None:
        # Mostrar imagem
        st.image(uploaded_file, caption="Imagem carregada", width=300)

        # Opções de análise
        options = st.radio(
            "Escolha o tipo de análise:", ["Análise simples", "Geração de planejamento"]
        )

        # Descrição adicional se for planejamento
        description = ""
        if options == "Geração de planejamento":
            description = st.text_area(
                "Descrição adicional para o planejamento:",
                placeholder="Ex: Planejar uma viagem para este destino",
            )

        if st.button("Analisar Imagem"):
            add_log(f"Iniciando análise de imagem: {options}")

            with st.spinner("Processando imagem..."):
                try:
                    # Obter serviço
                    image_service = st.session_state.image_analysis_service

                    if options == "Análise simples":
                        # Análise simples
                        resultado = image_service.analyze_image(uploaded_file)
                        log_success("Análise de imagem concluída com sucesso")

                        # Exibir resultado
                        st.subheader("Resultado da Análise")
                        st.write(resultado)

                    else:
                        # Geração de planejamento
                        resultado = image_service.generate_planning_from_image(
                            uploaded_file, description=description
                        )
                        log_success("Plano gerado com sucesso")

                        # Exibir resultado
                        st.subheader("Plano Gerado")
                        st.write(resultado)

                        # Armazenar o resultado
                        st.session_state.last_result = resultado

                except Exception as e:
                    log_error(f"Erro na análise: {str(e)}")
                    st.error(f"Ocorreu um erro: {str(e)}")

# Informações sobre o serviço
with st.expander("Sobre este serviço"):
    st.write(
        """
    Este é um serviço de análise de imagem que utiliza:

    1. **Análise simples**: Descrição das características da imagem
    2. **Geração de planejamento**: Criação de um plano baseado no conteúdo da imagem

    Para utilizar os outros serviços modularizados individualmente, acesse:
    - Planejamento: http://localhost:8508
    - Tarefas: http://localhost:8509
    """
    )
