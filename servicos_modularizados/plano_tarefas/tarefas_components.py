"""
Componentes de tarefas para o módulo plano_tarefas.
Versão local independente dos componentes originais de tarefas.
"""

import streamlit as st
import json
import re
import uuid
from datetime import datetime
import os
import sys

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
except ImportError:
    # Funções padrão para uso quando as importações falham
    def log_success(message):
        print(f"SUCCESS: {message}")

    def log_error(message):
        print(f"ERROR: {message}")


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

        return True
    except Exception as e:
        log_error(f"Erro ao criar tarefas do plano: {str(e)}")
        ui.error(f"Não foi possível criar tarefas: {str(e)}")
        return False


def exibir_tarefa(tarefa, index, container=None):
    """
    Exibe uma tarefa na interface com opções para marcar como concluída e excluir.
    """
    # Escolher onde renderizar
    ui = container if container else st

    # Usar um expander para cada tarefa
    tarefa_titulo = tarefa.get("titulo", "Tarefa sem título")

    # Mostrar ícone de estado (✅ ou ⬜️)
    status_icon = "✅" if tarefa.get("completed", False) else "⬜️"

    with ui.expander(f"{status_icon} {tarefa_titulo}"):
        cols = ui.columns([4, 1])

        with cols[0]:
            # Mostrar detalhes da tarefa
            ui.markdown(f"**Descrição:** {tarefa.get('descricao', 'Sem descrição')}")
            ui.markdown(f"**Prioridade:** {tarefa.get('prioridade', 'Normal')}")

            # Mostrar subtarefas se existirem
            if "subtarefas" in tarefa and tarefa["subtarefas"]:
                ui.markdown("**Subtarefas:**")

                # Usar um dataframe para exibir subtarefas com checkbox
                for subtarefa in tarefa["subtarefas"]:
                    subcols = ui.columns([0.1, 3.9])
                    with subcols[0]:
                        sub_completed = subtarefa.get("completed", False)
                        if ui.checkbox(
                            "", value=sub_completed, key=f"sub_{subtarefa['id']}"
                        ):
                            if not sub_completed:
                                subtarefa["completed"] = True
                                st.rerun()

                    with subcols[1]:
                        sub_status = "~~" if subtarefa.get("completed", False) else ""
                        ui.markdown(
                            f"{sub_status}{subtarefa.get('titulo', 'Subtarefa')}{sub_status}"
                        )

        with cols[1]:
            # Ações da tarefa
            if not tarefa.get("completed", False):
                if ui.button("Concluir", key=f"complete_{tarefa['id']}"):
                    tarefa["completed"] = True
                    st.rerun()
            else:
                if ui.button("Reabrir", key=f"reopen_{tarefa['id']}"):
                    tarefa["completed"] = False
                    st.rerun()

            if ui.button("Excluir", key=f"delete_{tarefa['id']}"):
                # Remover a tarefa da lista
                if index < len(st.session_state.tasks):
                    st.session_state.tasks.pop(index)
                    st.rerun()


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

    # Exibir lista de tarefas
    if "tasks" not in st.session_state or not st.session_state.tasks:
        ui.info(
            "Nenhuma tarefa criada. Use a aba 'Geração de Planejamento' para criar um plano e gerar tarefas."
        )
    else:
        ui.subheader(f"Suas Tarefas ({len(st.session_state.tasks)})")

        # Opções de visualização
        view = ui.radio(
            "Visualizar:",
            ["Todas", "Pendentes", "Concluídas"],
            horizontal=True,
            key="task_view",
        )

        # Filtrar tarefas conforme seleção
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

        ui.write(f"Mostrando {len(filtered_tasks)} tarefas")

        # Exibir tarefas
        for i, tarefa in enumerate(filtered_tasks):
            exibir_tarefa(tarefa, st.session_state.tasks.index(tarefa), container=ui)

        # Botão para limpar todas as tarefas
        if ui.button("Limpar Todas as Tarefas"):
            if ui.warning("Tem certeza? Esta ação não pode ser desfeita."):
                st.session_state.tasks = []
                st.rerun()
