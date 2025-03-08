"""
Aplicação integrada de planejamento e tarefas.
Este módulo integra os serviços de planejamento e gerenciamento de tarefas.
"""

import streamlit as st
import os
import sys
from datetime import datetime

# Configurar página - DEVE SER O PRIMEIRO COMANDO STREAMLIT!
st.set_page_config(page_title="Planejamento e Tarefas", page_icon="📋", layout="wide")

# Adicionar caminhos para importação
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SERVICES_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GERAL_DIR = os.path.join(SERVICES_DIR, "geral")

# Adicionar diretórios ao path
for path in [ROOT_DIR, SERVICES_DIR, GERAL_DIR]:
    if path not in sys.path:
        sys.path.insert(0, path)


# Funções de log padrão para uso quando os módulos não estiverem disponíveis
def log_success_default(message):
    print(f"SUCCESS: {message}")


def log_error_default(message):
    print(f"ERROR: {message}")


def log_warning_default(message):
    print(f"WARNING: {message}")


def get_logs_default(max_count=20):
    return []


def clear_logs_default():
    pass


# Inicializar variáveis com valores padrão
log_success = log_success_default
log_error = log_error_default
log_warning = log_warning_default
get_logs = get_logs_default
clear_logs = clear_logs_default
components_loaded = False

# Tentar importar os componentes dos módulos
try:
    # Tentar importar o logger
    try:
        from geral.app_logger import (
            log_success,
            log_error,
            log_warning,
            get_logs,
            clear_logs,
        )
    except ImportError as e:
        print(f"Aviso: Não foi possível importar logger: {str(e)}")

    # Tentar importar o histórico de planos - Novo módulo independente
    try:
        # Primeiro testar o novo módulo independente
        from historico_planos import (
            save_plan_to_history,
            get_plans_history,
            clear_plans_history,
        )

        log_success("Módulo de histórico de planos carregado com sucesso")
    except ImportError as e:
        print(f"Aviso: Módulo independente de histórico não encontrado: {str(e)}")
        # Fallback para implementação anterior
        try:
            from geral.planos_history_component import (
                save_plan_to_history,
            )

            log_success("Componente legado de histórico carregado com sucesso")
        except ImportError as e:
            print(f"Aviso: Nenhum componente de histórico disponível: {str(e)}")
            save_plan_to_history = None

    # Tentar importar componentes locais (nossos novos módulos)
    try:
        # Primeiro tentar os módulos locais
        from planejamento_components import planning_ui
        from tarefas_components import tasks_ui, criar_tarefas_do_plano

        log_success("Componentes locais carregados com sucesso")
    except ImportError as e:
        print(f"Aviso: Componentes locais não encontrados: {str(e)}")

        # Se falhar, tentar os módulos externos como fallback
        try:
            # Tentativa de usar módulos externos (legacy)
            from planejamento.components import planning_ui
            from tarefas.components import tasks_ui, criar_tarefas_do_plano

            log_success("Componentes externos carregados com sucesso")
        except ImportError as e:
            print(f"Erro: Não foi possível carregar componentes: {str(e)}")
            planning_ui = None
            tasks_ui = None
            criar_tarefas_do_plano = None

    components_loaded = True
except Exception as e:
    components_loaded = False
    print(f"Erro ao importar componentes: {str(e)}")


# Função para criar tarefas a partir do plano atual
def criar_tarefas_do_plano_atual():
    if "last_plan" in st.session_state and st.session_state.last_plan:
        try:
            # Verificar se a função está disponível
            if criar_tarefas_do_plano:
                # Criar as tarefas usando a função do módulo de tarefas
                if criar_tarefas_do_plano(st.session_state.last_plan):
                    log_success("Tarefas criadas com sucesso a partir do plano")
                    st.session_state.last_plan = (
                        None  # Limpar o plano após criar tarefas
                    )
                    st.success("Tarefas criadas com sucesso!")
                    st.rerun()
                    return True
            else:
                log_error("Módulo de tarefas não disponível")
                st.error("Módulo de tarefas não disponível")
                return False
        except Exception as e:
            log_error(f"Erro ao criar tarefas: {str(e)}")
            st.error(f"Erro ao criar tarefas: {str(e)}")
            return False
    else:
        log_error("Nenhum plano disponível para criar tarefas")
        st.warning("Nenhum plano disponível para criar tarefas")
        return False


# Título da página
st.title("📋 Planejamento e Tarefas")
st.write(
    "Esta aplicação integra os serviços de planejamento e gerenciamento de tarefas."
)

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

# Seção de Geração de Planejamento
st.markdown("---")
st.header("🔍 Geração de Planejamento")

if components_loaded and planning_ui:
    try:
        # Usar o componente de planejamento
        plan_image, plan_result = planning_ui()

        # Se gerou um plano, armazenar para uso posterior e criar tarefas automaticamente
        if plan_result:
            st.session_state.last_plan = plan_result
            log_success("Plano armazenado para uso")

            # Extrair título do plano se possível
            plano_titulo = "Plano Gerado"
            try:
                import json
                import re

                # Verificar se é um JSON ou texto com JSON embutido
                json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", plan_result)
                plano_json = json_match.group(1) if json_match else plan_result

                # Tentar carregar como JSON
                plano_data = json.loads(plano_json)
                plano_titulo = plano_data.get("titulo", "Plano Gerado")

                # Adicionar ao histórico usando o componente modularizado
                plano_info = {
                    "titulo": plano_titulo,
                    "json": plano_json,
                    "data": datetime.now().isoformat(),
                }

                # Salvar no histórico (session_state e Firestore) se a função estiver disponível
                if save_plan_to_history:
                    save_plan_to_history(plano_info)
                else:
                    # Fallback: salvar apenas na session_state
                    if "planos_historico" not in st.session_state:
                        st.session_state.planos_historico = []
                    st.session_state.planos_historico.append(plano_info)

            except Exception as e:
                # Se falhar, ainda assim adicionar ao histórico como texto
                plano_info = {
                    "titulo": "Plano Gerado",
                    "json": plan_result,
                    "data": datetime.now().isoformat(),
                }

                # Salvar no histórico se a função estiver disponível
                if save_plan_to_history:
                    save_plan_to_history(plano_info)
                else:
                    # Fallback: salvar apenas na session_state
                    if "planos_historico" not in st.session_state:
                        st.session_state.planos_historico = []
                    st.session_state.planos_historico.append(plano_info)

            # Criar tarefas automaticamente sem necessidade de clique adicional
            criar_tarefas_do_plano_atual()

    except Exception as e:
        log_error(f"Erro ao usar componente de planejamento: {str(e)}")
        st.error(f"Ocorreu um erro: {str(e)}")
else:
    st.error("Não foi possível carregar os componentes de planejamento.")

# Seção de Tarefas Geradas
st.markdown("---")
st.header("✅ Tarefas Geradas")

if components_loaded and tasks_ui:
    try:
        # Usar o componente de tarefas
        tasks_ui()
    except Exception as e:
        log_error(f"Erro ao usar componente de tarefas: {str(e)}")
        st.error(f"Ocorreu um erro: {str(e)}")
else:
    st.error("Não foi possível carregar os componentes de tarefas.")

# Informações sobre o aplicativo
with st.expander("Sobre este aplicativo"):
    st.write(
        """
    **Planejamento e Tarefas** integra dois módulos especializados:

    1. **Geração de Planejamento**: Criação de planos com base em descrições e imagens
    2. **Tarefas Geradas**: Gerenciamento de tarefas criadas a partir dos planos

    Esta aplicação permite o fluxo completo desde a criação do plano até
    o acompanhamento e conclusão das tarefas.
    """
    )
