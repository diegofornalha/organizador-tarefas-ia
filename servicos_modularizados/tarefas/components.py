"""
Componentes reutilizáveis para gerenciamento de tarefas.
Este módulo contém componentes de UI que podem ser compartilhados.
"""

import streamlit as st
import json
import re
import uuid
from datetime import datetime
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
from geral.history_service import HistoryService


def criar_tarefas_do_plano(plan_data=None, container=None):
    """
    Cria tarefas a partir de um plano JSON.

    Args:
        plan_data: Dados do plano em formato JSON ou texto com JSON embutido.
                  Se None, usa st.session_state.last_plan.
        container: Opcional, container streamlit para renderizar mensagens.
                  Se None, usa st diretamente.

    Returns:
        bool: True se as tarefas foram criadas com sucesso, False caso contrário.
    """
    # Escolher onde renderizar mensagens
    ui = container if container else st

    # Se não tiver dados do plano, tentar ler de session_state
    if not plan_data and "last_plan" in st.session_state:
        plan_data = st.session_state.last_plan

    # Se ainda não tiver plano, avisar e retornar False
    if not plan_data:
        ui.warning(
            "Nenhum plano disponível. Gere um plano primeiro na aba 'Geração de Planejamento'."
        )
        return False

    try:
        plan_text = plan_data if isinstance(plan_data, str) else json.dumps(plan_data)

        # Extrair o JSON se estiver em um código markdown
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", plan_text)
        if json_match:
            json_content = json_match.group(1)
            plan_data = json.loads(json_content)
        else:
            # Tentar carregar diretamente
            plan_data = json.loads(plan_text)

        # Verificar se o plano tem o formato esperado
        if "tarefas" not in plan_data:
            ui.error("O plano não tem o formato esperado.")
            return False

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

        # Inicializar a lista de tarefas se não existir
        if "tasks" not in st.session_state:
            st.session_state.tasks = []

        # Adicionar as novas tarefas à lista existente
        st.session_state.tasks.extend(novas_tarefas)
        log_success(
            f"Adicionadas {len(novas_tarefas)} tarefas do plano '{plano_titulo}'"
        )

        # Limpar o plano para evitar duplicação
        if "last_plan" in st.session_state:
            st.session_state.last_plan = None

        return True
    except Exception as e:
        log_error(f"Erro ao criar tarefas do plano: {str(e)}")
        ui.error(f"Não foi possível criar tarefas: {str(e)}")
        return False


def exibir_tarefa(tarefa, index, container=None):
    """
    Exibe uma tarefa na interface com opções para marcar como concluída e excluir.

    Args:
        tarefa: Dicionário com os dados da tarefa
        index: Índice da tarefa na lista completa
        container: Container Streamlit opcional. Se None, usa st diretamente.
    """
    # Escolher onde renderizar
    ui = container if container else st

    with ui.container():
        cols = ui.columns([1, 8, 1])

        # Status (concluída ou não)
        with cols[0]:
            completada = tarefa.get("completed", False)
            # Checkbox para marcar como concluída
            if ui.checkbox("", value=completada, key=f"check_{tarefa['id']}"):
                if not completada:
                    tarefa["completed"] = True
                    ui.success("Tarefa concluída!")
                    ui.rerun()

        # Detalhes da tarefa
        with cols[1]:
            # Título e descrição
            if completada:
                ui.markdown(f"#### ~~{tarefa['titulo']}~~")
            else:
                ui.markdown(f"#### {tarefa['titulo']}")

            if tarefa.get("descricao"):
                ui.markdown(f"{tarefa['descricao']}")

            # Prioridade
            prioridade = tarefa.get("prioridade", "média")
            ui.caption(f"Prioridade: {prioridade}")

            # Subtarefas
            if "subtarefas" in tarefa and tarefa["subtarefas"]:
                with ui.expander("Subtarefas"):
                    for i, subtarefa in enumerate(tarefa["subtarefas"]):
                        sub_cols = ui.columns([1, 11])
                        with sub_cols[0]:
                            sub_completed = subtarefa.get("completed", False)
                            if ui.checkbox(
                                "", value=sub_completed, key=f"sub_{subtarefa['id']}"
                            ):
                                if not sub_completed:
                                    subtarefa["completed"] = True
                                    ui.success("Subtarefa concluída!")
                                    ui.rerun()

                        with sub_cols[1]:
                            if sub_completed:
                                ui.markdown(f"~~{subtarefa['titulo']}~~")
                            else:
                                ui.markdown(f"{subtarefa['titulo']}")

                            if subtarefa.get("descricao"):
                                ui.caption(subtarefa["descricao"])

        # Botões de ação
        with cols[2]:
            if ui.button("🗑️", key=f"del_{tarefa['id']}"):
                st.session_state.tasks.pop(index)
                log_success(f"Tarefa '{tarefa['titulo']}' removida")
                ui.rerun()

        ui.divider()


def tasks_ui(container=None):
    """
    Renderiza a interface de gerenciamento de tarefas em um container
    ou diretamente na página se container=None.

    Args:
        container: Opcional, container streamlit para renderizar o componente.
                  Se None, usa st diretamente.
    """
    # Escolher onde renderizar
    ui = container if container else st

    # Botão para criar tarefas a partir do plano existente
    if "last_plan" in st.session_state and st.session_state.last_plan:
        if ui.button("Criar Tarefas do Plano Atual"):
            if criar_tarefas_do_plano(st.session_state.last_plan, container=ui):
                ui.success("Tarefas criadas com sucesso!")
                ui.rerun()

    # Exibir lista de tarefas
    if "tasks" not in st.session_state or not st.session_state.tasks:
        ui.info(
            "Nenhuma tarefa criada. Use a aba 'Geração de Planejamento' para criar um plano e gerar tarefas."
        )
    else:
        ui.subheader(f"Suas Tarefas ({len(st.session_state.tasks)})")

        # Opções de visualização
        view_options = ["Todas", "Pendentes", "Concluídas"]
        view = ui.radio("Visualizar:", view_options, horizontal=True)

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
            exibir_tarefa(tarefa, st.session_state.tasks.index(tarefa), container=ui)

        # Botão para limpar todas as tarefas
        if ui.button("Limpar Todas as Tarefas"):
            st.session_state.tasks = []
            log_success("Todas as tarefas foram removidas")
            ui.rerun()


def tasks_standalone():
    """
    Versão standalone da interface de gerenciamento de tarefas.
    Usado quando este módulo é executado diretamente.
    """
    import streamlit as st
    from geral.app_logger import get_logs, clear_logs

    # Configurar página
    st.set_page_config(
        page_title="Gerenciamento de Tarefas", page_icon="✅", layout="wide"
    )

    # Título da página
    st.title("✅ Gerenciamento de Tarefas")
    st.write("Ferramenta para organizar e acompanhar tarefas.")

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
    st.header("Suas Tarefas")

    # Usar o componente reutilizável
    tasks_ui()

    # Informações sobre o módulo
    with st.expander("Sobre esta ferramenta"):
        st.write(
            """
        Esta é uma versão modular do serviço de gerenciamento de tarefas.
        Ela permite organizar e acompanhar tarefas geradas a partir de planos.

        Funcionalidades:
        1. **Visualização de tarefas** (todas, pendentes ou concluídas)
        2. **Marcação de tarefas** como concluídas
        3. **Gerenciamento de subtarefas**
        4. **Remoção de tarefas** individuais ou todas de uma vez

        As tarefas são armazenadas na sessão atual do navegador.
        """
        )
