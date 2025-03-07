"""
Aplicação integrada de planejamento e tarefas.
Este módulo integra os serviços de planejamento e gerenciamento de tarefas.
"""

import streamlit as st
import os
import sys
from dotenv import load_dotenv
from datetime import datetime

# Configurar página - DEVE SER O PRIMEIRO COMANDO STREAMLIT!
st.set_page_config(page_title="Planejamento e Tarefas", page_icon="📋", layout="wide")

# Adicionar caminhos para importação
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SERVICES_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLANNING_DIR = os.path.join(SERVICES_DIR, "planejamento")
TASKS_DIR = os.path.join(SERVICES_DIR, "tarefas")
GERAL_DIR = os.path.join(SERVICES_DIR, "geral")

# Adicionar diretórios ao path
for path in [ROOT_DIR, SERVICES_DIR, PLANNING_DIR, TASKS_DIR, GERAL_DIR]:
    if path not in sys.path:
        sys.path.insert(0, path)

# Importar os componentes dos módulos
try:
    from planejamento.components import planning_ui
    from tarefas.components import tasks_ui, criar_tarefas_do_plano
    from geral.app_logger import add_log, log_success, log_error, get_logs, clear_logs

    components_loaded = True
    log_success("Componentes carregados com sucesso")
except ImportError as e:
    components_loaded = False
    print(f"Erro ao importar componentes: {str(e)}")

# Carregar variáveis de ambiente
load_dotenv()


# Função para criar tarefas a partir do plano atual
def criar_tarefas_do_plano_atual():
    if "last_plan" in st.session_state and st.session_state.last_plan:
        try:
            # Criar as tarefas usando a função do módulo de tarefas
            if criar_tarefas_do_plano(st.session_state.last_plan):
                log_success("Tarefas criadas com sucesso a partir do plano")
                st.session_state.last_plan = None  # Limpar o plano após criar tarefas
                st.success("Tarefas criadas com sucesso!")
                st.rerun()
                return True
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

# Inicializar histórico de planos na session_state se não existir
if "planos_historico" not in st.session_state:
    st.session_state.planos_historico = []

# Barra lateral para histórico de planos
with st.sidebar:
    # Botão para Nova Consulta
    if st.button("🔄 Nova Consulta", use_container_width=True):
        # Limpar o formulário e estado atual
        if "last_plan" in st.session_state:
            st.session_state.last_plan = None

        # Forçar recarregamento da página
        st.rerun()

    st.header("📚 Histórico de Planos")

    if not st.session_state.planos_historico:
        st.info("Nenhum plano foi gerado ainda.")
    else:
        st.write(f"Total de planos: {len(st.session_state.planos_historico)}")

        # Exibir planos em acordeões
        for i, plano_info in enumerate(st.session_state.planos_historico):
            with st.expander(f"Plano #{i+1}: {plano_info.get('titulo', 'Sem título')}"):
                st.text_area(
                    "JSON do Plano",
                    value=plano_info.get("json", "{}"),
                    height=200,
                    disabled=True,
                    key=f"plano_json_{i}",
                )

    # Botão para limpar histórico
    if st.session_state.planos_historico and st.button("Limpar Histórico"):
        st.session_state.planos_historico = []
        st.success("Histórico de planos limpo!")
        st.rerun()

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

if components_loaded:
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

                # Adicionar ao histórico
                st.session_state.planos_historico.append(
                    {
                        "titulo": plano_titulo,
                        "json": plano_json,
                        "data": datetime.now().isoformat(),
                    }
                )
            except Exception as json_error:
                # Se falhar, ainda assim adicionar ao histórico como texto
                st.session_state.planos_historico.append(
                    {
                        "titulo": "Plano Gerado",
                        "json": plan_result,
                        "data": datetime.now().isoformat(),
                    }
                )

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

if components_loaded:
    try:
        # Remover botão adicional - as tarefas já devem ter sido criadas automaticamente
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
