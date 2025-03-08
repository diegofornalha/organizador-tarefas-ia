"""
Componente reutilizável para histórico de planos.
Permite visualizar, gerenciar e interagir com o histórico de planos
gerados em qualquer aplicativo que utilize este componente.
"""

import streamlit as st
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable

# Importar serviços necessários
try:
    from .app_logger import log_success, log_error, log_warning
    from .firestore_service import firestore_service
except ImportError:
    # Caso falhe, tenta importar diretamente (quando executado como script)
    from app_logger import log_success, log_error, log_warning
    from firestore_service import firestore_service


def show_plans_history_sidebar(
    on_new_query_click: Optional[Callable] = None, container=None
):
    """
    Exibe o histórico de planos na barra lateral.

    Args:
        on_new_query_click: Função a ser chamada quando o botão "Nova Consulta" for clicado
        container: Container onde o componente será renderizado (opcional)
    """
    # Escolher onde renderizar
    ui = container if container else st.sidebar

    # Botão para Nova Consulta
    if ui.button("🔄 Nova Consulta", use_container_width=True):
        # Limpar o formulário e estado atual
        if "last_plan" in st.session_state:
            st.session_state.last_plan = None

        # Chamar função de callback, se fornecida
        if on_new_query_click:
            on_new_query_click()

        # Forçar recarregamento da página
        st.rerun()

    ui.header("📚 Histórico de Planos")

    # Carregar histórico
    _ensure_plans_history_loaded()

    if not st.session_state.planos_historico:
        ui.info("Nenhum plano foi gerado ainda.")
    else:
        ui.write(f"Total de planos: {len(st.session_state.planos_historico)}")

        # Exibir planos em acordeões
        for i, plano_info in enumerate(st.session_state.planos_historico):
            with ui.expander(f"Plano #{i+1}: {plano_info.get('titulo', 'Sem título')}"):
                ui.text_area(
                    "JSON do Plano",
                    value=plano_info.get("json", "{}"),
                    height=200,
                    disabled=True,
                    key=f"plano_json_{i}",
                )

    # Botão para limpar histórico
    if st.session_state.planos_historico and ui.button("Limpar Histórico"):
        _clear_plans_history()
        ui.success("Histórico de planos limpo!")
        st.rerun()


def save_plan_to_history(plan_data: Dict[str, Any]) -> bool:
    """
    Salva um plano no histórico (tanto na session_state quanto no Firestore).

    Args:
        plan_data: Dados do plano (deve conter título e json)

    Returns:
        bool: True se salvo com sucesso
    """
    try:
        # Verificar se já temos o histórico inicializado
        _ensure_plans_history_loaded()

        # Adicionar ao histórico local
        st.session_state.planos_historico.append(plan_data)

        # Salvar no Firestore também
        try:
            firestore_service.save_plan_to_history(plan_data)
        except Exception as e:
            log_error(f"Erro ao salvar plano no Firestore: {str(e)}")

        return True

    except Exception as e:
        log_error(f"Erro ao salvar plano no histórico: {str(e)}")
        return False


def _ensure_plans_history_loaded():
    """
    Garante que o histórico de planos está carregado na session_state.
    Se não estiver, tenta carregar do Firestore.
    """
    if "planos_historico" not in st.session_state:
        st.session_state.planos_historico = []

        # Tentar carregar do Firestore
        try:
            planos_firestore = firestore_service.get_plans_history()
            if planos_firestore:
                # Converter para o formato usado na session_state
                for plano in planos_firestore:
                    st.session_state.planos_historico.append(
                        {
                            "titulo": plano.get("titulo", "Plano sem título"),
                            "json": plano.get("json", "{}"),
                            "data": plano.get("created_at", datetime.now().isoformat()),
                        }
                    )
                log_success(
                    f"Carregados {len(planos_firestore)} planos do histórico do Firestore"
                )
        except Exception as e:
            log_error(f"Erro ao carregar histórico do Firestore: {str(e)}")


def _clear_plans_history():
    """
    Limpa o histórico de planos da session_state e do Firestore.
    """
    st.session_state.planos_historico = []

    # Limpar também no Firestore
    try:
        if firestore_service.clear_plans_history():
            log_success("Histórico de planos limpo também no Firestore")
    except Exception as e:
        log_error(f"Erro ao limpar histórico no Firestore: {str(e)}")
