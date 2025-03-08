"""
Interface principal do orquestrador.
Este script implementa uma interface para gerenciar os módulos do sistema.
"""

import os
import sys
import io
import uuid
import socket
import contextlib
from datetime import datetime
import subprocess
from dotenv import load_dotenv
import json
import re

# Carregar variáveis de ambiente
load_dotenv()

# Configurar page_config primeiro (DEVE ser a primeira chamada Streamlit)
import streamlit as st

st.set_page_config(page_title="Orquestrador de Módulos", page_icon="🔌", layout="wide")

# Lista para armazenar logs
initialization_logs = []
system_logs = []

# Importar módulos - usando importações diretas
from app_logger import add_log, log_success, log_error, get_logs, clear_logs
from module_registry import module_registry, initialize_registry

# Sobrescrever funções padrão de notificação do Streamlit para capturar logs
original_success = st.success
original_info = st.info
original_warning = st.warning
original_error = st.error

# Import para os componentes de plano_tarefas - APÓS a configuração da página
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "servicos_modularizados",
    ),
)
try:
    from servicos_modularizados.plano_tarefas.planejamento_components import planning_ui
    from servicos_modularizados.plano_tarefas.tarefas_components import (
        tasks_ui,
        criar_tarefas_do_plano,
    )
except ImportError:
    planning_ui = None
    tasks_ui = None
    criar_tarefas_do_plano = None

# Import para os componentes de historico_planos
servicos_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "servicos_modularizados"
)
if servicos_path not in sys.path:
    sys.path.insert(0, servicos_path)

try:
    from servicos_modularizados.historico_planos import (
        show_plans_history_sidebar,
        show_plans_history_panel,
        save_plan_to_history,
    )
except ImportError:
    show_plans_history_sidebar = None
    show_plans_history_panel = None
    save_plan_to_history = None

# Import para os componentes de historico_tarefas
try:
    from servicos_modularizados.historico_tarefas import (
        show_tasks_history_sidebar,
        show_tasks_history_panel,
        show_tasks_analytics,
        record_task_event,
    )
except ImportError:
    show_tasks_history_sidebar = None
    show_tasks_history_panel = None
    show_tasks_analytics = None
    record_task_event = None


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


# Substituir todas as funções de notificação do Streamlit pelas versões silenciosas
# Isso fará com que todas as mensagens sejam registradas nos logs, mas não exibidas na interface
st.success = silent_success
st.info = silent_info
st.warning = silent_warning
st.error = silent_error


# Função para obter logs combinados
def get_combined_logs(max_count=50):
    combined_logs = initialization_logs + system_logs
    return combined_logs[-max_count:] if combined_logs else []


# Função para limpar todos os logs
def clear_all_logs():
    initialization_logs.clear()
    system_logs.clear()
    if callable(clear_logs):
        clear_logs()


# Inicializar o registro de módulos com captura de logs
registry = capture_output(initialize_registry)()

# Definição de portas para cada módulo
MODULE_PORTS = {
    "plano_tarefas": 8511,
    "analise_imagem": 8507,
    "historico_planos": 8512,
    "historico_tarefas": 8513,
    "geral": 8510,
}

# Definição dos ícones para cada módulo
MODULE_ICONS = {
    "plano_tarefas": "📋",
    "analise_imagem": "🔍",
    "historico_planos": "📚",
    "historico_tarefas": "📝",
    "geral": "🧩",
}

# Título da página
st.title("🔌 Orquestrador de Módulos")
st.write("Interface para gerenciamento dos módulos do sistema.")

# Logs do sistema (recolhidos por padrão)
with st.expander("Logs do Sistema", expanded=False):
    # Adicionar botão de limpar
    cols = st.columns([4, 1])
    with cols[1]:
        if st.button("Limpar Logs"):
            clear_all_logs()
            # Usamos o original_success diretamente para esta única notificação
            if original_success is not None:
                original_success("Logs limpos")
            st.rerun()

    # Mostrar todos os logs
    logs = get_combined_logs(max_count=50)
    if logs:
        for log in logs:
            st.text(log)
    else:
        # Usamos o original_info diretamente
        if original_info is not None:
            original_info("Nenhum log disponível.")
        else:
            st.write("Nenhum log disponível.")

# Histórico de Planos na barra lateral
if show_plans_history_sidebar is not None:
    # Adicionar histórico de planos na barra lateral
    with st.sidebar:
        st.header("📚 historico_planos")
        # Botão de nova consulta ACIMA do divider
        if st.button("🔍 Nova Consulta", key="nova_consulta_planos"):
            # Limpar o formulário e estado atual
            if "last_plan" in st.session_state:
                st.session_state.last_plan = None
            # Forçar recarregamento da página
            st.rerun()
        st.markdown("---")
        show_plans_history_sidebar()

# Histórico de Tarefas na barra lateral
if show_tasks_history_sidebar is not None:
    # Adicionar histórico de tarefas na barra lateral
    with st.sidebar:
        st.header("📝 historico_tarefas")
        # Botão de nova consulta ACIMA do divider
        if st.button("📊 Nova Consulta", key="nova_consulta_tarefas"):
            # Limpar qualquer estado relacionado a tarefas, se necessário
            # Forçar recarregamento da página
            st.rerun()
        st.markdown("---")
        show_tasks_history_sidebar()

# Layout principal com colunas
col1, col2 = st.columns([1, 2])


# Função para verificar se uma porta está em uso (serviço está rodando)
def check_port_in_use(port):
    """Verifica se uma porta está em uso, indicando que o serviço está rodando."""
    try:
        # Tenta criar uma conexão com a porta
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)  # Timeout curto para não travar a interface
            return (
                s.connect_ex(("localhost", port)) == 0
            )  # Retorna True se a porta estiver em uso
    except:
        return False


# Função para atualizar status dos módulos baseado nas portas ativas
def update_module_status():
    """Atualiza o status dos módulos verificando se seus serviços estão rodando nas portas definidas."""
    for module_name, port in MODULE_PORTS.items():
        module_info = registry.get_module(module_name)
        if module_info and not module_info.is_loaded:
            # Se o módulo existe, não está marcado como carregado, mas a porta está em uso
            if check_port_in_use(port) or (
                module_name == "plano_tarefas" and check_port_in_use(8511)
            ):
                system_logs.append(
                    f"INFO: Serviço '{module_name}' detectado rodando na porta {port if module_name != 'plano_tarefas' else 8511}"
                )
                module_info.is_loaded = True
                # Força um carregamento automático do módulo no registro
                if not module_info.module_instance:
                    try:
                        registry.load_module(module_name)
                    except Exception:
                        pass  # Ignora erros, o importante é marcar como carregado


# Atualizar status dos módulos antes de mostrar a interface
update_module_status()

# Verificação específica para o módulo plano_tarefas
plano_tarefas_module = registry.get_module("plano_tarefas")
if plano_tarefas_module and not plano_tarefas_module.is_loaded:
    # Se o serviço estiver rodando na porta 8511, marcar como carregado
    if check_port_in_use(8511):
        system_logs.append(
            "INFO: Forçando carregamento do módulo 'plano_tarefas' que está rodando na porta 8511"
        )
        plano_tarefas_module.is_loaded = True
        # Forçar carregamento do módulo no registro se possível
        try:
            registry.load_module("plano_tarefas")
        except Exception:
            pass  # Ignora erros, o importante é marcar como carregado

# Coluna 1 - Lista de módulos disponíveis
with col1:
    st.header("Módulos Disponíveis")

    col_buttons = st.columns(2)
    with col_buttons[0]:
        if st.button("Detectar Módulos", key="detect_modules"):
            detect_logs = []
            with contextlib.redirect_stdout(io.StringIO()) as output:
                modules = registry.discover_modules()
                capture_output = output.getvalue()
                for line in capture_output.splitlines():
                    if line.strip():
                        detect_logs.append(line)
                        system_logs.append(line)

            st.write(f"✅ Detectados {len(modules)} módulos")

    with col_buttons[1]:
        if st.button("Atualizar Status", key="refresh_status"):
            update_module_status()
            st.write("✅ Status dos módulos atualizado")
            system_logs.append("INFO: Status dos módulos atualizado manualmente")
            st.rerun()

    # Listar módulos disponíveis
    available_modules = registry.list_available_modules()

    if not available_modules:
        st.write("⚠️ Nenhum módulo disponível. Clique em 'Detectar Módulos'.")
    else:
        for module_name in available_modules:
            module = registry.get_module(module_name)
            if module is None:
                continue

            is_loaded = module.is_loaded

            col_mod1, col_mod2, col_mod3 = st.columns([3, 1, 1])
            with col_mod1:
                icon = MODULE_ICONS.get(module_name, "📦")
                if is_loaded:
                    st.markdown(f"✅ **{icon} {module_name}**")
                else:
                    st.markdown(f"⬜ {icon} {module_name}")

            with col_mod2:
                if not is_loaded:
                    if st.button("Carregar", key=f"load_{module_name}"):
                        load_logs = []
                        with contextlib.redirect_stdout(io.StringIO()) as output:
                            success = registry.load_module(module_name)
                            capture_output = output.getvalue()
                            for line in capture_output.splitlines():
                                if line.strip():
                                    load_logs.append(line)
                                    system_logs.append(line)

                        if success:
                            st.write(f"✅ Módulo {module_name} carregado!")
                            st.rerun()
                        else:
                            st.write(f"❌ Erro ao carregar {module_name}")
                else:
                    st.text("Carregado")

            with col_mod3:
                port = MODULE_PORTS.get(module_name)
                if port:
                    if st.button("Executar", key=f"run_{module_name}"):
                        st.markdown(f"[Abrir {module_name}](http://localhost:{port})")
                        st.write(f"🔗 Serviço disponível na porta {port}")

# Coluna 2 - Detalhes do módulo selecionado
with col2:
    st.header("Detalhes do Módulo")

    # Seletor de módulo
    if available_modules:
        selected_module = st.selectbox("Selecione um módulo:", available_modules)

        module_info = registry.get_module(selected_module)

        if module_info:
            # Mostrar detalhes do módulo
            icon = MODULE_ICONS.get(selected_module, "📦")
            st.markdown(f"### {icon} {module_info.name}")
            st.write(f"**Descrição:** {module_info.description}")
            st.write(f"**Versão:** {module_info.version}")
            st.write(f"**Caminho:** {module_info.path}")

            # Status do módulo
            status = "Carregado" if module_info.is_loaded else "Não carregado"
            st.write(f"**Status:** {status}")

            # Portas e URLs
            port = MODULE_PORTS.get(selected_module)
            if port:
                st.write(f"**Porta:** {port}")
                st.write(f"**URL:** http://localhost:{port}")

                col_actions1, col_actions2 = st.columns(2)
                with col_actions1:
                    if not module_info.is_loaded:
                        if st.button(
                            "Carregar Módulo", key=f"load_detail_{selected_module}"
                        ):
                            with contextlib.redirect_stdout(io.StringIO()) as output:
                                success = registry.load_module(selected_module)
                                capture_output = output.getvalue()
                                for line in capture_output.splitlines():
                                    if line.strip():
                                        system_logs.append(line)

                            if success:
                                st.write(f"✅ Módulo {selected_module} carregado!")
                                st.rerun()
                            else:
                                st.write(f"❌ Erro ao carregar {selected_module}")
                    else:
                        st.write("✅ Módulo carregado com sucesso!")

                with col_actions2:
                    if st.button("Abrir no Navegador", key=f"open_{selected_module}"):
                        st.markdown(
                            f"[Clique aqui para abrir {selected_module}](http://localhost:{port})"
                        )

            # Dependências
            if module_info.dependencies:
                with st.expander("Dependências", expanded=False):
                    for dep in module_info.dependencies:
                        dep_info = registry.get_module(dep)
                        dep_loaded = dep_info and dep_info.is_loaded
                        st.write(f"- {dep} {'✅' if dep_loaded else '❌'}")

            # Componentes exportados
            if module_info.is_loaded and module_info.exported_components:
                with st.expander("Componentes Exportados", expanded=False):
                    for name, component in module_info.exported_components.items():
                        st.write(f"- **{name}**: `{type(component).__name__}`")

                        # Se for uma função ou método, mostrar informações adicionais
                        if callable(component):
                            try:
                                import inspect

                                signature = inspect.signature(component)
                                st.code(f"{name}{signature}")
                            except Exception:
                                pass
            elif module_info.is_loaded:
                with st.expander("Componentes Exportados", expanded=False):
                    st.write("ℹ️ Nenhum componente exportado encontrado")
            else:
                with st.expander("Componentes Exportados", expanded=False):
                    st.write("⚠️ Carregue o módulo para ver componentes")

# Área de módulos
st.header("Módulos do Sistema")

# Atualizar status dos módulos sempre que a página é carregada
update_module_status()

# Criar abas dinâmicas para os módulos disponíveis
if available_modules:
    # Primeiro, ordenar por status de carregamento
    sorted_modules = sorted(
        [m for m in available_modules if registry.get_module(m)],
        key=lambda m: not registry.get_module(m).is_loaded,
    )

    # Definir ordem específica para todos os módulos
    def custom_sort_key(m):
        order = {
            "geral": 0,
            "plano_tarefas": 1,
            "analise_imagem": 2,
            "historico_planos": 3,
            "historico_tarefas": 4,
        }
        # Retorna a posição definida ou um valor alto para módulos não listados
        return order.get(m, 100)

    sorted_modules = sorted(sorted_modules, key=custom_sort_key)

    tabs = st.tabs([f"{MODULE_ICONS.get(m, '📦')} {m}" for m in sorted_modules])

    for i, module_name in enumerate(sorted_modules):
        with tabs[i]:
            module_info = registry.get_module(module_name)
            if not module_info:
                st.write(f"❌ Módulo {module_name} não encontrado")
                continue

            # Mostrar status e ações
            if not module_info.is_loaded:
                st.write(f"⚠️ Módulo {module_name} não está carregado")
                if st.button("Carregar módulo", key=f"load_tab_{module_name}"):
                    with contextlib.redirect_stdout(io.StringIO()) as output:
                        success = registry.load_module(module_name)
                        capture_output = output.getvalue()
                        for line in capture_output.splitlines():
                            if line.strip():
                                system_logs.append(line)

                    if success:
                        st.write(f"✅ Módulo {module_name} carregado!")
                        st.rerun()
                    else:
                        st.write(f"❌ Erro ao carregar {module_name}")
            else:
                st.write(f"✅ Módulo {module_name} está carregado")

                # Opções específicas do módulo
                if module_name == "plano_tarefas":
                    st.subheader("Planejamento e Tarefas")
                    st.write("Este módulo permite criar e gerenciar planos e tarefas.")

                    # Verificar se os componentes necessários estão disponíveis
                    if planning_ui is None or tasks_ui is None:
                        st.error(
                            "Não foi possível carregar os componentes necessários."
                        )
                        port = MODULE_PORTS.get(module_name)
                        if port:
                            st.markdown(
                                f"[Acessar aplicação completa](http://localhost:{port})"
                            )
                    else:
                        # Interface completa com abas

                        # Determinar qual aba deve estar ativa
                        if "active_tab" not in st.session_state:
                            st.session_state.active_tab = "planejamento"

                        # Botões para controlar a navegação entre abas
                        tab_options = ["Planejamento", "Histórico de Planos"]

                        # Exibir botões de navegação apenas se não estiver na seção de histórico de planos
                        if st.session_state.active_tab != "historico":
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button(
                                    "📝 Planejamento",
                                    use_container_width=True,
                                    type=(
                                        "primary"
                                        if st.session_state.active_tab == "planejamento"
                                        else "secondary"
                                    ),
                                ):
                                    st.session_state.active_tab = "planejamento"
                                    st.rerun()
                            with col2:
                                if st.button(
                                    "📚 Histórico",
                                    use_container_width=True,
                                    type=(
                                        "primary"
                                        if st.session_state.active_tab == "historico"
                                        else "secondary"
                                    ),
                                ):
                                    st.session_state.active_tab = "historico"
                                    st.rerun()

                        # Mostrar conteúdo baseado na aba ativa
                        if st.session_state.active_tab == "planejamento":
                            st.header("📝 Planejamento")
                            # Usar o componente de planejamento
                            planning_container = st.container()
                            plan_result = planning_ui(planning_container)

                            # O planning_ui retorna uma tupla (plan_image, plan_result)
                            # Precisamos extrair o plan_result (texto JSON ou resposta)
                            if (
                                plan_result
                                and isinstance(plan_result, tuple)
                                and len(plan_result) == 2
                            ):
                                plan_image, plan_text = plan_result

                                # Se temos um plano, tentar processá-lo
                                if plan_text:
                                    try:
                                        # Tentar extrair JSON do texto se estiver entre ```json e ```
                                        json_match = re.search(
                                            r"```(?:json)?\s*([\s\S]*?)\s*```",
                                            plan_text,
                                        )

                                        if json_match:
                                            json_content = json_match.group(1)
                                            plan_data = json.loads(json_content)
                                        else:
                                            # Tentar carregar diretamente como JSON
                                            plan_data = json.loads(plan_text)

                                        # Agora temos um plan_data como dicionário que podemos processar
                                        if "current_plan" not in st.session_state:
                                            st.session_state.current_plan = plan_data
                                        elif st.session_state.current_plan.get(
                                            "id", ""
                                        ) != plan_data.get("id", ""):
                                            st.session_state.current_plan = plan_data

                                        # Salvar no histórico (se disponível)
                                        if save_plan_to_history is not None:
                                            try:
                                                save_plan_to_history(plan_data)
                                                log_success("Plano salvo no histórico")

                                                # Mostrar mensagem de sucesso sem mudar para a aba de histórico
                                                st.success(
                                                    "✅ Plano salvo no histórico com sucesso! As tarefas estão disponíveis abaixo."
                                                )
                                                # Não mudamos mais de aba, permanecemos na tela com as tarefas
                                                # st.session_state.active_tab = "historico"
                                                # st.rerun()
                                            except Exception as e:
                                                log_error(
                                                    f"Erro ao salvar plano no histórico: {str(e)}"
                                                )

                                        # Verificar se temos a função para criar tarefas
                                        if criar_tarefas_do_plano is not None:
                                            criar_tarefas_do_plano(plan_data)
                                    except Exception as e:
                                        log_error(f"Erro ao processar plano: {str(e)}")
                                        st.error(
                                            f"Não foi possível processar o plano: {str(e)}"
                                        )

                                # Adicionar uma separação visual antes das tarefas
                                st.markdown("---")

                                # Seção de tarefas abaixo do planejamento
                                st.header("✅ Tarefas")
                                # Verificar se temos um plano selecionado
                                current_plan = st.session_state.get(
                                    "current_plan", None
                                )

                                if current_plan:
                                    st.write(
                                        f"📘 Plano atual: **{current_plan.get('title', 'Sem título')}**"
                                    )

                                # Usar o componente de tarefas
                                tasks_container = st.container()
                                tasks_ui(tasks_container)

                        elif st.session_state.active_tab == "historico":
                            st.header("📚 Histórico de Planos")
                            # Verificar se o componente de histórico está disponível
                            if show_plans_history_panel is not None:
                                # Usar o componente de histórico de planos
                                history_container = st.container()
                                show_plans_history_panel(history_container)
                            else:
                                st.error(
                                    "Componente de histórico de planos não disponível"
                                )
                                st.write(
                                    "Verifique se o módulo historico_planos está instalado corretamente"
                                )
                                port_historico = MODULE_PORTS.get("historico_planos")
                                if port_historico:
                                    st.markdown(
                                        f"[Acessar histórico completo](http://localhost:{port_historico})"
                                    )

                elif module_name == "analise_imagem":
                    st.subheader("Análise de Imagem")
                    st.write(
                        "Este módulo permite analisar imagens e gerar planejamentos a partir delas."
                    )

                    # Upload de imagem
                    uploaded_file = st.file_uploader(
                        "Escolha uma imagem",
                        type=["jpg", "jpeg", "png"],
                        key=f"image_uploader_{module_name}",
                    )

                    if uploaded_file:
                        st.image(uploaded_file, caption="Imagem carregada", width=300)

                        if st.button("Analisar imagem", key=f"analyze_{module_name}"):
                            st.write(
                                "ℹ️ Funcionalidade de análise está disponível na aplicação completa"
                            )
                            port = MODULE_PORTS.get(module_name)
                            if port:
                                st.markdown(
                                    f"[Abrir aplicação de análise](http://localhost:{port})"
                                )

                    port = MODULE_PORTS.get(module_name)
                    if port:
                        if st.button(
                            "Iniciar aplicação", key=f"start_app_{module_name}"
                        ):
                            st.markdown(f"[Abrir aplicação](http://localhost:{port})")
                            st.write(f"🔗 Serviço disponível na porta {port}")

                elif module_name == "historico_planos":
                    st.subheader("📚 historico_planos")
                    st.write("Este módulo gerencia o histórico de planos gerados.")

                    # Verificar se o componente de histórico está disponível
                    if show_plans_history_panel is not None:
                        # Usar o componente de histórico de planos
                        history_container = st.container()
                        show_plans_history_panel(history_container)
                    else:
                        st.error("Componente de histórico de planos não disponível")
                        st.write(
                            "Verifique se o módulo historico_planos está instalado corretamente"
                        )
                        port = MODULE_PORTS.get(module_name)
                        if port:
                            st.markdown(
                                f"[Abrir aplicação completa](http://localhost:{port})"
                            )
                            st.write(f"🔗 Serviço disponível na porta {port}")

                elif module_name == "historico_tarefas":
                    st.subheader("📝 historico_tarefas")
                    st.write(
                        "Este módulo gerencia o histórico de tarefas criadas e executadas."
                    )

                    # Verificar se os componentes de histórico estão disponíveis
                    if (
                        show_tasks_history_panel is not None
                        and show_tasks_analytics is not None
                    ):
                        # Criar abas para diferentes visualizações
                        history_tab, analytics_tab = st.tabs(
                            ["Histórico de Tarefas", "Análises de Produtividade"]
                        )

                        # Tab 1: Histórico de Tarefas
                        with history_tab:
                            history_container = st.container()
                            show_tasks_history_panel(history_container)

                        # Tab 2: Análises
                        with analytics_tab:
                            analytics_container = st.container()
                            show_tasks_analytics(analytics_container)
                    else:
                        st.error("Componentes de histórico de tarefas não disponíveis")
                        st.write(
                            "Verifique se o módulo historico_tarefas está instalado corretamente"
                        )
                        port = MODULE_PORTS.get(module_name)
                        if port:
                            st.markdown(
                                f"[Abrir aplicação completa](http://localhost:{port})"
                            )
                            st.write(f"🔗 Serviço disponível na porta {port}")

                elif module_name == "geral":
                    st.subheader("Componentes Reutilizáveis")
                    st.write(
                        "Este módulo contém componentes e serviços compartilhados."
                    )

                    # Mostrar os componentes disponíveis
                    components = module_info.exported_components
                    if components:
                        with st.expander("Componentes Disponíveis", expanded=False):
                            for name, component in sorted(components.items()):
                                st.write(f"- **{name}**: `{type(component).__name__}`")
                    else:
                        st.write("ℹ️ Nenhum componente exportado encontrado")

                # Componentes exportados (para qualquer módulo)
                with st.expander("Componentes Exportados", expanded=False):
                    components = module_info.exported_components
                    if components:
                        for name, component in sorted(components.items()):
                            st.write(f"- **{name}**: `{type(component).__name__}`")

                            # Se for uma função ou método, mostrar informações adicionais
                            if callable(component):
                                try:
                                    import inspect

                                    signature = inspect.signature(component)
                                    st.code(f"{name}{signature}")
                                except Exception:
                                    pass
                    else:
                        st.write("ℹ️ Nenhum componente exportado encontrado")

# Informações sobre o sistema
with st.expander("Sobre o Orquestrador", expanded=False):
    st.write(
        """
    ## Orquestrador de Módulos

    Este componente funciona como um hub central que:

    1. **Importa e integra serviços** de outros módulos
    2. **Fornece interfaces unificadas** para esses serviços
    3. **Disponibiliza componentes compartilhados**
    4. **Orquestra a interação** entre os módulos

    Para utilizar os serviços modularizados individualmente, acesse:
    - Planejamento: http://localhost:8508
    - Tarefas: http://localhost:8509
    - Análise de Imagem: http://localhost:8507
    """
    )

# Restaurar as funções originais do Streamlit ao final do script
st.success = original_success
st.info = original_info
st.warning = original_warning
st.error = original_error
