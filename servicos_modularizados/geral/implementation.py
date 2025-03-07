"""
Script para testar a implementação do serviço de análise de imagem e planejamento.
"""

import streamlit as st
import json
import re
import uuid
from datetime import datetime
from dotenv import load_dotenv
import sys
import os

# Configurar página - DEVE SER O PRIMEIRO COMANDO STREAMLIT!
st.set_page_config(page_title="Teste de Serviços", page_icon="🧪", layout="wide")

# Importar módulos - usando importações diretas
from app_logger import add_log, log_success, log_error, get_logs, clear_logs
from image_analysis_service import ImageAnalysisService
from history_service import HistoryService

# Tentar importar os componentes reutilizáveis
try:
    # Adicionar caminho para o módulo analise_imagem se não estiver no PYTHONPATH
    analise_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "analise_imagem"
    )
    if analise_path not in sys.path:
        sys.path.append(analise_path)

    # Importar os componentes
    from analise_imagem.components import image_analysis_ui

    has_components = True
    log_success("Componentes de análise de imagem importados com sucesso")
except ImportError as e:
    has_components = False
    log_error(f"Não foi possível importar componentes: {str(e)}")

# Carregar variáveis de ambiente
load_dotenv()

# Inicializar estado da sessão
if "tasks" not in st.session_state:
    st.session_state.tasks = []

if "last_plan" not in st.session_state:
    st.session_state.last_plan = None

# Inicializar aba ativa (0=análise, 1=planejamento, 2=tarefas)
if "active_tab" not in st.session_state:
    st.session_state.active_tab = 0

# Inicializar serviços
if "image_analysis_service" not in st.session_state:
    try:
        st.session_state.image_analysis_service = ImageAnalysisService(debug_mode=True)
        st.session_state.debug_mode = True
        log_success("Serviço de análise de imagem inicializado")
    except Exception as e:
        log_error(f"Erro ao inicializar serviço de análise de imagem: {str(e)}")


# Função para mudar de aba programaticamente
def mudar_para_aba(index):
    st.session_state.active_tab = index
    add_log(f"Mudando para aba {index}")


# Título da página
st.title("🧪 Teste de Serviços")
st.write("Esta página testa os serviços de análise de imagem e planejamento.")

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

# Tabs para os testes
tab1, tab2, tab3 = st.tabs(
    ["Teste de Análise de Imagem", "Geração de Planejamento", "Tarefas do Planejamento"]
)

# Selecionar a aba ativa
tab_index = st.session_state.active_tab
tab_list = [tab1, tab2, tab3]
active_tab = tab_list[tab_index]

# Tab de Análise de Imagem
with tab1:
    if tab_index == 0:
        st.header("Teste de Análise de Imagem")

        # Verificar se podemos usar o componente reutilizável
        if has_components:
            try:
                # Usar o componente diretamente
                uploaded_file, result = image_analysis_ui()

                # Se tiver um resultado e for um plano, armazenar para uso na aba de tarefas
                if result and uploaded_file and "planejamento" in str(result).lower():
                    st.session_state.last_plan = result
                    log_success("Plano armazenado para uso na aba de tarefas")
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

            # Código original continua aqui em caso de falha na importação
            if uploaded_file is not None:
                # Mostrar imagem
                st.image(uploaded_file, caption="Imagem carregada", width=300)

                # Opções de análise
                options = st.radio(
                    "Escolha o tipo de análise:",
                    ["Análise simples", "Geração de planejamento"],
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

                                # Armazenar o plano para uso na aba de tarefas
                                st.session_state.last_plan = resultado

                        except Exception as e:
                            log_error(f"Erro na análise: {str(e)}")

# Tab de Geração de Planejamento
with tab2:
    if tab_index == 1:
        st.header("Geração de Planejamento de Tarefas")

        col1, col2 = st.columns([3, 2])

        with col1:
            # Descrição do projeto/tarefa
            st.subheader("Descrição do Projeto")
            project_description = st.text_area(
                "Descreva o projeto ou tarefa a ser planejado:",
                placeholder="Ex: Organizar uma festa de aniversário para 30 pessoas",
                height=150,
            )

            # Upload de imagem relacionada (opcional)
            st.subheader("Imagem de Referência (Opcional)")
            plan_image = st.file_uploader(
                "Selecione uma imagem de referência para o planejamento",
                type=["jpg", "jpeg", "png"],
                key="planning_uploader",
            )

            if plan_image:
                st.image(plan_image, caption="Imagem de referência", width=300)

            # Opções adicionais
            st.subheader("Opções Adicionais")
            detailed_plan = st.checkbox("Plano detalhado", value=True)

            # Guardar o estado do checkbox de cronograma
            include_timeline_key = "include_timeline_checkbox"
            if include_timeline_key not in st.session_state:
                st.session_state[include_timeline_key] = False

            include_timeline = st.checkbox(
                "Incluir cronograma",
                value=st.session_state[include_timeline_key],
                key=include_timeline_key,
            )

            # Botão para gerar o plano
            if st.button("Gerar Plano de Tarefas"):
                if not project_description:
                    st.error("Por favor, forneça uma descrição do projeto.")
                else:
                    with st.spinner("Gerando plano de tarefas..."):
                        try:
                            # Obter serviço
                            image_service = st.session_state.image_analysis_service

                            # Preparar descrição completa
                            full_description = project_description
                            if detailed_plan:
                                full_description += "\n\nPor favor, forneça um plano detalhado com tarefas e subtarefas."
                            if include_timeline:
                                full_description += "\n\nInclua um cronograma sugerido para cada tarefa."

                            # Gerar o plano (com ou sem imagem)
                            if plan_image:
                                plan_result = (
                                    image_service.generate_planning_from_image(
                                        plan_image, description=full_description
                                    )
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

                            # Armazenar o plano para uso na aba de tarefas
                            st.session_state.last_plan = plan_result

                            # Registrar no histórico
                            try:
                                history_service = HistoryService()
                                history_service.register_plan_generation(
                                    full_description, plan_image is not None
                                )
                            except Exception:
                                pass

                            # Exibir resultado na outra coluna
                            with col2:
                                st.subheader("Plano Gerado")
                                st.write(plan_result)

                                # Tentar extrair JSON se existir
                                try:
                                    json_content = plan_result

                                    # Extrair apenas o JSON (pode estar entre ```json e ```)
                                    json_match = re.search(
                                        r"```(?:json)?\s*([\s\S]*?)\s*```", json_content
                                    )
                                    if json_match:
                                        json_content = json_match.group(1)

                                    # Tentar carregar como JSON
                                    plano = json.loads(json_content)

                                    if "tarefas" in plano:
                                        st.subheader("Visualização Estruturada")
                                        st.write(
                                            f"**{plano.get('titulo', 'Plano de Tarefas')}**"
                                        )
                                        st.write(plano.get("descricao", ""))

                                        for i, tarefa in enumerate(plano["tarefas"]):
                                            tarefa_titulo = tarefa["titulo"]
                                            tarefa_prio = tarefa.get(
                                                "prioridade", "média"
                                            )
                                            with st.expander(
                                                f"{i+1}. {tarefa_titulo} ({tarefa_prio})"
                                            ):
                                                st.write(tarefa.get("descricao", ""))
                                                if (
                                                    "subtarefas" in tarefa
                                                    and tarefa["subtarefas"]
                                                ):
                                                    st.write("**Subtarefas:**")
                                                    for j, subtarefa in enumerate(
                                                        tarefa["subtarefas"]
                                                    ):
                                                        st.write(
                                                            f"- {subtarefa['titulo']}"
                                                        )

                                        # Botão para ir para a aba de tarefas
                                        if st.button(
                                            "Criar Tarefas a partir deste Plano"
                                        ):
                                            # Mudar para a tab de tarefas usando a função
                                            mudar_para_aba(2)
                                            st.rerun()
                                except Exception:
                                    # Se não conseguir extrair JSON, apenas mostrar o texto
                                    pass

                        except Exception as e:
                            log_error(f"Erro ao gerar plano: {str(e)}")
                            st.error(f"Não foi possível gerar o plano: {str(e)}")

# Tab de Tarefas do Planejamento
with tab3:
    if tab_index == 2:
        st.header("Gerenciamento de Tarefas")

        # Função para criar tarefas a partir do plano
        def criar_tarefas_do_plano():
            if not st.session_state.last_plan:
                st.warning(
                    "Nenhum plano disponível. Gere um plano primeiro na aba 'Geração de Planejamento'."
                )
                return

            try:
                plan_text = st.session_state.last_plan

                # Extrair o JSON se estiver em um código markdown
                json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", plan_text)
                if json_match:
                    json_content = json_match.group(1)
                    plan_data = json.loads(json_content)
                else:
                    plan_data = json.loads(plan_text)

                # Verificar se o plano tem o formato esperado
                if "tarefas" not in plan_data:
                    st.error("O plano não tem o formato esperado.")
                    return

                # Criar tarefas
                plano_titulo = plan_data.get("titulo", "Plano sem título")
                novas_tarefas = []

                for tarefa_data in plan_data["tarefas"]:
                    # Criar ID único para a tarefa
                    tarefa_id = str(uuid.uuid4())

                    # Criar tarefa
                    tarefa = {
                        "id": tarefa_id,
                        "titulo": tarefa_data["titulo"],
                        "descricao": tarefa_data.get("descricao", ""),
                        "prioridade": tarefa_data.get("prioridade", "média"),
                        "created_at": datetime.now().isoformat(),
                        "completed": False,
                    }

                    # Adicionar subtarefas se existirem
                    if "subtarefas" in tarefa_data and tarefa_data["subtarefas"]:
                        tarefa["subtarefas"] = []
                        for subtarefa_data in tarefa_data["subtarefas"]:
                            subtarefa = {
                                "id": str(uuid.uuid4()),
                                "titulo": subtarefa_data["titulo"],
                                "descricao": subtarefa_data.get("descricao", ""),
                                "completed": False,
                            }
                            tarefa["subtarefas"].append(subtarefa)

                    novas_tarefas.append(tarefa)

                # Adicionar as novas tarefas à lista existente
                st.session_state.tasks.extend(novas_tarefas)
                log_success(
                    f"Adicionadas {len(novas_tarefas)} tarefas do plano '{plano_titulo}'"
                )

                # Limpar o plano para evitar duplicação
                st.session_state.last_plan = None

                return True
            except Exception as e:
                log_error(f"Erro ao criar tarefas do plano: {str(e)}")
                st.error(f"Não foi possível criar tarefas: {str(e)}")
                return False

        # Função para exibir uma tarefa
        def exibir_tarefa(tarefa, index):
            with st.container():
                cols = st.columns([1, 8, 1])

                # Status (concluída ou não)
                with cols[0]:
                    completada = tarefa.get("completed", False)
                    # Checkbox para marcar como concluída
                    if st.checkbox("", value=completada, key=f"check_{tarefa['id']}"):
                        if not completada:
                            tarefa["completed"] = True
                            st.success("Tarefa concluída!")
                            st.rerun()

                # Detalhes da tarefa
                with cols[1]:
                    # Título e descrição
                    if completada:
                        st.markdown(f"#### ~~{tarefa['titulo']}~~")
                    else:
                        st.markdown(f"#### {tarefa['titulo']}")

                    if tarefa.get("descricao"):
                        st.markdown(f"{tarefa['descricao']}")

                    # Prioridade
                    prioridade = tarefa.get("prioridade", "média")
                    st.caption(f"Prioridade: {prioridade}")

                    # Subtarefas
                    if "subtarefas" in tarefa and tarefa["subtarefas"]:
                        with st.expander("Subtarefas"):
                            for i, subtarefa in enumerate(tarefa["subtarefas"]):
                                sub_cols = st.columns([1, 11])
                                with sub_cols[0]:
                                    sub_completed = subtarefa.get("completed", False)
                                    if st.checkbox(
                                        "",
                                        value=sub_completed,
                                        key=f"sub_{subtarefa['id']}",
                                    ):
                                        if not sub_completed:
                                            subtarefa["completed"] = True
                                            st.success("Subtarefa concluída!")
                                            st.rerun()

                                with sub_cols[1]:
                                    if sub_completed:
                                        st.markdown(f"~~{subtarefa['titulo']}~~")
                                    else:
                                        st.markdown(f"{subtarefa['titulo']}")

                                    if subtarefa.get("descricao"):
                                        st.caption(subtarefa["descricao"])

                # Botões de ação
                with cols[2]:
                    if st.button("🗑️", key=f"del_{tarefa['id']}"):
                        st.session_state.tasks.pop(index)
                        log_success(f"Tarefa '{tarefa['titulo']}' removida")
                        st.rerun()

                st.divider()

        # Botão para criar tarefas a partir do plano existente
        if st.session_state.last_plan:
            if st.button("Criar Tarefas do Plano Atual"):
                if criar_tarefas_do_plano():
                    st.success("Tarefas criadas com sucesso!")
                    st.rerun()

        # Exibir lista de tarefas
        if not st.session_state.tasks:
            st.info(
                "Nenhuma tarefa criada. Use a aba 'Geração de Planejamento' para criar um plano e gerar tarefas."
            )
        else:
            st.subheader(f"Suas Tarefas ({len(st.session_state.tasks)})")

            # Opções de visualização
            view_options = ["Todas", "Pendentes", "Concluídas"]
            view = st.radio("Visualizar:", view_options, horizontal=True)

            # Filtrar tarefas conforme a visualização
            filtered_tasks = []
            if view == "Todas":
                filtered_tasks = st.session_state.tasks
            elif view == "Pendentes":
                filtered_tasks = [
                    t for t in st.session_state.tasks if not t.get("completed", False)
                ]
            else:  # Concluídas
                filtered_tasks = [
                    t for t in st.session_state.tasks if t.get("completed", False)
                ]

            # Exibir tarefas
            for i, tarefa in enumerate(filtered_tasks):
                exibir_tarefa(tarefa, st.session_state.tasks.index(tarefa))

            # Botão para limpar todas as tarefas
            if st.button("Limpar Todas as Tarefas"):
                st.session_state.tasks = []
                log_success("Todas as tarefas foram removidas")
                st.rerun()
