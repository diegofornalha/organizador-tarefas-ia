"""
Aplicação integrada de planejamento e tarefas.
Este módulo integra os serviços de planejamento e gerenciamento de tarefas.
"""

import streamlit as st
import os
import sys
import io
from datetime import datetime

# Lista para armazenar logs de inicialização (apenas para depuração interna)
initialization_logs = []
system_logs = []

# Sobrescrever funções padrão de notificação do Streamlit para capturar logs
original_success = st.success
original_info = st.info
original_warning = st.warning
original_error = st.error

# Configurar página - DEVE SER O PRIMEIRO COMANDO STREAMLIT!
st.set_page_config(page_title="Planejamento e Tarefas", page_icon="📋", layout="wide")


# Função para capturar saída padrão (para logs)
def capture_output(func):
    def wrapper(*args, **kwargs):
        # Redirecionar stdout para capturar saída
        old_stdout = sys.stdout
        captured_output = io.StringIO()
        sys.stdout = captured_output

        # Executar função
        result = func(*args, **kwargs)

        # Restaurar stdout e capturar saída
        sys.stdout = old_stdout
        output = captured_output.getvalue()

        # Armazenar cada linha como um log separado
        for line in output.splitlines():
            if line.strip():  # Ignorar linhas vazias
                initialization_logs.append(line)

        return result

    return wrapper


# Sobrescrever funções de notificação do Streamlit para capturar e não exibir
def silent_success(message, *args, **kwargs):
    system_logs.append(f"SUCCESS: {message}")
    # Não chamar a função original para não exibir a notificação


def silent_info(message, *args, **kwargs):
    system_logs.append(f"INFO: {message}")
    # Não chamar a função original para não exibir a notificação


def silent_warning(message, *args, **kwargs):
    system_logs.append(f"WARNING: {message}")
    # Não chamar a função original para não exibir a notificação


def silent_error(message, *args, **kwargs):
    system_logs.append(f"ERROR: {message}")
    # Não chamar a função original para não exibir a notificação


# Adicionar caminhos para importação
root_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
services_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
geral_path = os.path.join(services_path, "geral")

# Adicionar diretórios ao path
for path in [root_path, services_path, geral_path]:
    if path not in sys.path:
        sys.path.insert(0, path)


# Funções de log padrão para uso quando os módulos não estiverem disponíveis
def log_success_default(message):
    print(f"SUCCESS: {message}")
    initialization_logs.append(f"SUCCESS: {message}")
    system_logs.append(f"SUCCESS: {message}")


def log_error_default(message):
    print(f"ERROR: {message}")
    initialization_logs.append(f"ERROR: {message}")
    system_logs.append(f"ERROR: {message}")


def log_warning_default(message):
    print(f"WARNING: {message}")
    initialization_logs.append(f"WARNING: {message}")
    system_logs.append(f"WARNING: {message}")


def get_logs_default(max_count=20):
    combined_logs = initialization_logs + system_logs
    return combined_logs[-max_count:] if combined_logs else []


def clear_logs_default():
    initialization_logs.clear()
    system_logs.clear()


# Inicializar variáveis com valores padrão
log_success = log_success_default
log_error = log_error_default
log_warning = log_warning_default
get_logs = get_logs_default
clear_logs = clear_logs_default
components_loaded = False
save_plan_to_history = None

# Sobrescrever funções do Streamlit para evitar notificações
st.success = silent_success
st.info = silent_info
st.warning = silent_warning
st.error = silent_error


# Tentar importar os componentes dos módulos
@capture_output
def load_components():
    global log_success, log_error, log_warning, get_logs, clear_logs
    global components_loaded, save_plan_to_history

    # Tentar importar o logger
    try:
        from geral.app_logger import (
            log_success,
            log_error,
            log_warning,
            get_logs,
            clear_logs,
        )
    except ImportError:
        print("Aviso: Não foi possível importar logger")

    # Tentar importar o histórico de planos
    try:
        # Primeiro testar o novo módulo independente
        from historico_planos import save_plan_to_history

        print("Módulo de histórico de planos carregado com sucesso")
    except ImportError:
        print("Aviso: Módulo independente de histórico não encontrado")
        # Fallback para implementação anterior
        try:
            from geral.planos_history_component import save_plan_to_history

            print("Componente legado de histórico carregado com sucesso")
        except ImportError:
            print("Aviso: Nenhum componente de histórico disponível")
            save_plan_to_history = None

    components_loaded = True
    return components_loaded


# Carregar componentes
load_components()

# Restaurar funções originais do Streamlit para uso na interface (apenas para alguns elementos)
st_success_selective = original_success
st_error_selective = original_error

# Interface do usuário
st.title("📋 Planejamento e Tarefas")
st.write("Aplicação integrada para planejamento e gerenciamento de tarefas.")

# Componente de logs do sistema (recolhido por padrão)
with st.expander("Logs do Sistema", expanded=False):
    # Adicionar botão de limpar
    cols = st.columns([4, 1])
    with cols[1]:
        if original_success is not None and original_success != st.success:
            if st.button("Limpar Logs"):
                clear_logs()
                # Aqui usamos o original_success diretamente para esta única notificação
                original_success("Logs limpos")
                st.rerun()

    # Mostrar logs do sistema (se disponíveis)
    if "get_logs" in globals() and callable(get_logs):
        logs = get_logs(max_count=50)
        if logs:
            for log in logs:
                st.text(log)
        else:
            # Aqui usamos o original_info diretamente para esta única notificação
            if original_info is not None and original_info != st.info:
                original_info("Nenhum log disponível.")
            else:
                st.write("Nenhum log disponível.")
    else:
        # Aqui usamos o original_warning diretamente para esta única notificação
        if original_warning is not None and original_warning != st.warning:
            original_warning("Função de logs não disponível.")
        else:
            st.write("⚠️ Função de logs não disponível.")

# Verificar se os componentes foram carregados
if not components_loaded:
    # Aqui usamos o original_error diretamente para esta única notificação crítica
    if original_error is not None and original_error != st.error:
        original_error("Não foi possível carregar todos os componentes necessários.")
    else:
        st.write("❌ Não foi possível carregar todos os componentes necessários.")
    st.stop()

# Interface principal com abas
tab1, tab2 = st.tabs(["Planejamento", "Tarefas"])

with tab1:
    st.header("📝 Planejamento")
    try:
        # Importar o componente sob demanda
        from planejamento_components import planning_ui

        # Usar o componente
        planning_container = st.container()
        plan_data = planning_ui(planning_container)

        # Se um plano foi criado, armazenar na sessão para uso em tarefas
        if plan_data and isinstance(plan_data, dict):
            if "current_plan" not in st.session_state:
                st.session_state.current_plan = plan_data
            elif st.session_state.current_plan.get("id") != plan_data.get("id"):
                st.session_state.current_plan = plan_data

            # Salvar no histórico (se disponível)
            if save_plan_to_history is not None:
                try:
                    save_plan_to_history(plan_data)
                    log_success("Plano salvo no histórico")
                except Exception as e:
                    log_error(f"Erro ao salvar plano no histórico: {str(e)}")
    except Exception as e:
        # Aqui usamos o original_error diretamente para esta única notificação crítica
        if original_error is not None and original_error != st.error:
            original_error(f"Erro ao carregar componente de planejamento: {str(e)}")
        else:
            st.write(f"❌ Erro ao carregar componente de planejamento: {str(e)}")

with tab2:
    st.header("✅ Tarefas")
    try:
        # Importar o componente sob demanda
        from tarefas_components import tasks_ui

        # Verificar se temos um plano selecionado
        current_plan = st.session_state.get("current_plan", None)

        if current_plan:
            # Evitando st.info diretamente
            st.write(f"📘 Plano atual: **{current_plan.get('title', 'Sem título')}**")

        # Usar o componente de tarefas
        tasks_container = st.container()
        # Passar apenas o ID do plano se o componente aceitar esse parâmetro
        try:
            if current_plan:
                tasks_ui(tasks_container, current_plan.get("id"))
            else:
                tasks_ui(tasks_container)
        except TypeError:
            # Se o componente não aceitar o ID, chamá-lo sem esse parâmetro
            tasks_ui(tasks_container)
    except Exception as e:
        # Aqui usamos o original_error diretamente para esta única notificação crítica
        if original_error is not None and original_error != st.error:
            original_error(f"Erro ao carregar componente de tarefas: {str(e)}")
        else:
            st.write(f"❌ Erro ao carregar componente de tarefas: {str(e)}")

# Rodapé
st.write("---")
st.write("© 2023 Aplicação de Planejamento e Tarefas")

# Exibir informações técnicas em expansor
with st.expander("Informações Técnicas", expanded=False):
    st.write("**Caminhos de Importação:**")
    for path in sys.path[:5]:  # Mostrar apenas os primeiros 5 caminhos
        st.code(path)

    st.write("**Variáveis de Sessão:**")
    session_vars = [str(var) for var in st.session_state.keys()]
    st.code(", ".join(session_vars))

# Restaurar as funções originais do Streamlit ao final do script
st.success = original_success
st.info = original_info
st.warning = original_warning
st.error = original_error
