"""
Componentes reutilizáveis para análise de imagem.
Este módulo contém componentes de UI que podem ser compartilhados.
"""

import streamlit as st
import os
import sys

# Adicionar caminhos para importação
SERVICES_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GERAL_DIR = os.path.join(SERVICES_DIR, "geral")

# Adicionar diretórios ao path se necessário
if GERAL_DIR not in sys.path:
    sys.path.insert(0, GERAL_DIR)

# Importar funcionalidades necessárias
from geral.app_logger import add_log, log_success, log_error
from geral.image_analysis_service import ImageAnalysisService


def image_analysis_ui(container=None):
    """
    Renderiza a interface de análise de imagem em um container
    ou diretamente na página se container=None.

    Args:
        container: Opcional, container streamlit para renderizar o componente.
                  Se None, usa st diretamente.

    Returns:
        Tuple: (uploaded_file, analysis_result) - A imagem carregada e o resultado da análise
    """
    # Escolher onde renderizar (container ou diretamente)
    ui = container if container else st

    result = None

    # Upload de imagem
    uploaded_file = ui.file_uploader(
        "Escolha uma imagem", type=["jpg", "jpeg", "png"], key="image_analysis_uploader"
    )

    if uploaded_file is not None:
        # Mostrar imagem
        ui.image(uploaded_file, caption="Imagem carregada", width=300)

        # Opções de análise
        options = ui.radio(
            "Escolha o tipo de análise:", ["Análise simples", "Geração de planejamento"]
        )

        # Descrição adicional se for planejamento
        description = ""
        if options == "Geração de planejamento":
            description = ui.text_area(
                "Descrição adicional para o planejamento:",
                placeholder="Ex: Planejar uma viagem para este destino",
            )

        if ui.button("Analisar Imagem"):
            add_log(f"Iniciando análise de imagem: {options}")

            with ui.spinner("Processando imagem..."):
                try:
                    # Garantir que o serviço exista na sessão
                    if "image_analysis_service" not in st.session_state:
                        st.session_state.image_analysis_service = ImageAnalysisService(
                            debug_mode=True
                        )

                    # Obter serviço
                    image_service = st.session_state.image_analysis_service

                    if options == "Análise simples":
                        # Análise simples
                        prompt = "Descreva esta imagem brevemente."
                        result = image_service.analyze_image(
                            uploaded_file, prompt=prompt
                        )
                        log_success("Análise de imagem concluída com sucesso")

                        # Exibir resultado
                        ui.subheader("Resultado da Análise")
                        ui.write(result)

                    else:
                        # Geração de planejamento
                        result = image_service.generate_planning_from_image(
                            uploaded_file, description=description
                        )
                        log_success("Plano gerado com sucesso")

                        # Exibir resultado
                        ui.subheader("Plano Gerado")
                        ui.write(result)

                        # Armazenar o plano para uso posterior
                        if "last_plan" not in st.session_state:
                            st.session_state.last_plan = result

                except Exception as e:
                    log_error(f"Erro na análise: {str(e)}")
                    ui.error(f"Ocorreu um erro durante a análise: {str(e)}")

    return uploaded_file, result


def image_analysis_standalone():
    """
    Versão standalone da interface de análise de imagem.
    Usado quando este módulo é executado diretamente.
    """
    import streamlit as st
    from geral.app_logger import get_logs, clear_logs

    # NÃO CONFIGURA MAIS A PÁGINA AQUI
    # A configuração deve estar no arquivo principal (image_analysis.py)

    # Título da página
    st.title("🔍 Análise de Imagem")
    st.write("Ferramenta para análise de imagem com IA.")

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
    st.header("Análise de Imagem")

    # Usar o componente reutilizável
    image_analysis_ui()

    # Informações sobre o módulo
    with st.expander("Sobre esta ferramenta"):
        st.write(
            """
        Esta é uma versão modular do serviço de análise de imagem.
        Ela contém apenas as funcionalidades essenciais:

        1. **Análise simples**: Descrição breve da imagem
        2. **Geração de planejamento**: Criação de um plano baseado na imagem

        Esta ferramenta pode ser integrada ao aplicativo principal.
        """
        )
