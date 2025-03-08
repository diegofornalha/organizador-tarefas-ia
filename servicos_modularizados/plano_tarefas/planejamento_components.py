"""
Componentes de planejamento para o módulo plano_tarefas.
Versão local independente dos componentes originais de planejamento.
"""

import streamlit as st
import json
import re
import os
import sys
from datetime import datetime

# Configurações de caminhos e imports
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICES_DIR = os.path.dirname(CURRENT_DIR)
GERAL_DIR = os.path.join(SERVICES_DIR, "geral")

# Adicionar diretórios ao path se necessário
if GERAL_DIR not in sys.path:
    sys.path.insert(0, GERAL_DIR)

# Importar funcionalidades necessárias
try:
    from geral.app_logger import log_success, log_error
    from geral.image_analysis_service import ImageAnalysisService
except ImportError:
    # Funções padrão para uso quando as importações falham
    def log_success(message):
        print(f"SUCCESS: {message}")

    def log_error(message):
        print(f"ERROR: {message}")

    # Classe básica para ImageAnalysisService
    class ImageAnalysisService:
        def __init__(self, debug_mode=False):
            self.debug_mode = debug_mode

        def analyze_image(self, image, prompt=None):
            return "Serviço de análise de imagem não disponível"

        def generate_planning_from_image(self, image, description=None):
            return "Serviço de planejamento a partir de imagem não disponível"


def planning_ui(container=None):
    """
    Renderiza a interface de geração de planejamento em um container
    ou diretamente na página se container=None.

    Args:
        container: Opcional, container streamlit para renderizar o componente.
                  Se None, usa st diretamente.

    Returns:
        Tuple: (plan_image, plan_result) - A imagem carregada e o resultado do planejamento
    """
    # Escolher onde renderizar (container ou diretamente)
    ui = container if container else st

    plan_result = None
    plan_image = None

    # Layout com duas colunas
    col1, col2 = ui.columns([3, 2])

    with col1:
        # Descrição do projeto/tarefa
        ui.subheader("Descrição do Projeto")
        project_description = ui.text_area(
            "Descreva o projeto ou tarefa a ser planejado:",
            placeholder="Ex: Organizar uma festa de aniversário para 30 pessoas",
            height=150,
        )

        # Upload de imagem relacionada (opcional)
        ui.subheader("Imagem de Referência (Opcional)")
        plan_image = ui.file_uploader(
            "Selecione uma imagem de referência para o planejamento",
            type=["jpg", "jpeg", "png"],
            key="planning_uploader",
        )

        if plan_image:
            ui.image(plan_image, caption="Imagem de referência", width=300)

        # Opções adicionais
        ui.subheader("Opções Adicionais")
        detailed_plan = ui.checkbox("Plano detalhado", value=True)

        # Guardar o estado do checkbox de cronograma
        include_timeline_key = "include_timeline_checkbox"
        if include_timeline_key not in st.session_state:
            st.session_state[include_timeline_key] = False

        include_timeline = ui.checkbox(
            "Incluir cronograma",
            value=st.session_state[include_timeline_key],
            key=include_timeline_key,
        )

        # Botão para gerar o plano
        if ui.button("Gerar Plano de Tarefas"):
            if not project_description:
                ui.error("Por favor, forneça uma descrição do projeto.")
            else:
                with ui.spinner("Gerando plano de tarefas..."):
                    try:
                        # Garantir que o serviço exista na sessão
                        if "image_analysis_service" not in st.session_state:
                            st.session_state.image_analysis_service = (
                                ImageAnalysisService(debug_mode=True)
                            )

                        # Obter serviço
                        image_service = st.session_state.image_analysis_service

                        # Preparar descrição completa
                        full_description = project_description
                        if detailed_plan:
                            full_description += "\n\nPor favor, forneça um plano detalhado com tarefas e subtarefas."
                        if include_timeline:
                            full_description += (
                                "\n\nInclua um cronograma sugerido para cada tarefa."
                            )

                        # Gerar o plano (com ou sem imagem)
                        if plan_image:
                            plan_result = image_service.generate_planning_from_image(
                                plan_image, description=full_description
                            )
                        else:
                            # Usar o mesmo serviço mas sem imagem
                            prompt = f"""
                            Você é um assistente especializado em organizar tarefas.
                            Com base na descrição fornecida, crie um plano detalhado
                            com tarefas, subtarefas e um cronograma.

                            Descrição: {full_description}

                            Organize sua resposta no seguinte formato JSON:
                            {{
                                "titulo": "Título do plano",
                                "descricao": "Descrição geral do plano",
                                "tarefas": [
                                    {{
                                        "titulo": "Título da tarefa 1",
                                        "descricao": "Descrição detalhada",
                                        "prioridade": "alta|média|baixa",
                                        "subtarefas": [
                                            {{
                                                "titulo": "Subtarefa 1.1",
                                                "descricao": "Descrição da subtarefa"
                                            }}
                                        ]
                                    }}
                                ]
                            }}
                            """
                            plan_result = image_service.analyze_image(
                                None, prompt=prompt
                            )

                        log_success("Plano de tarefas gerado com sucesso")

                        # Exibir resultado na outra coluna
                        with col2:
                            ui.subheader("Plano Gerado")
                            ui.write(plan_result)

                            # Tentar extrair JSON se existir
                            try:
                                json_content = plan_result

                                # Extrair apenas o JSON (pode estar entre ```json e ```)
                                json_match = re.search(
                                    r"```(?:json)?\s*([\s\S]*?)\s*```",
                                    json_content,
                                )
                                if json_match:
                                    json_content = json_match.group(1)

                                # Tentar carregar como JSON
                                plano = json.loads(json_content)

                                if "tarefas" in plano:
                                    ui.subheader("Visualização Estruturada")
                                    ui.write(
                                        f"**{plano.get('titulo', 'Plano de Tarefas')}**"
                                    )
                                    ui.write(plano.get("descricao", ""))

                                    for i, tarefa in enumerate(plano["tarefas"]):
                                        tarefa_titulo = tarefa["titulo"]
                                        tarefa_prio = tarefa.get("prioridade", "média")
                                        with ui.expander(
                                            f"{i+1}. {tarefa_titulo} ({tarefa_prio})"
                                        ):
                                            ui.write(tarefa.get("descricao", ""))
                                            if (
                                                "subtarefas" in tarefa
                                                and tarefa["subtarefas"]
                                            ):
                                                ui.write("**Subtarefas:**")
                                                for j, subtarefa in enumerate(
                                                    tarefa["subtarefas"]
                                                ):
                                                    ui.write(f"- {subtarefa['titulo']}")

                                    # Informar que as tarefas serão criadas automaticamente
                                    ui.success("Tarefas sendo criadas automaticamente!")
                            except Exception:
                                # Se não conseguir extrair JSON, apenas mostrar o texto
                                pass

                    except Exception as e:
                        log_error(f"Erro ao gerar plano: {str(e)}")
                        ui.error(f"Não foi possível gerar o plano: {str(e)}")

    return plan_image, plan_result
