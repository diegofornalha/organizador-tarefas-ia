"""
Componentes da barra lateral para o Organizador de Tarefas.
Este módulo contém componentes reutilizáveis para a barra lateral.
"""
import streamlit as st
from datetime import datetime
import pytz

# Importar serviços necessários
from .app_logger import log_success, log_error
from .history_service import HistoryService


def format_timestamp(timestamp_str: str) -> str:
    """
    Formata um timestamp ISO para exibição amigável

    Args:
        timestamp_str: String ISO de data/hora

    Returns:
        String formatada para exibição
    """
    try:
        dt = datetime.fromisoformat(timestamp_str)
        # Definir fuso horário para Brasil/São Paulo
        brasil_tz = pytz.timezone('America/Sao_Paulo')
        dt = dt.astimezone(brasil_tz)

        # Verificar se é hoje
        hoje = datetime.now(brasil_tz).date()
        if dt.date() == hoje:
            return f"Hoje às {dt.strftime('%H:%M')}"
        # Verificar se é ontem
        ontem = hoje.replace(day=hoje.day-1)
        if dt.date() == ontem:
            return f"Ontem às {dt.strftime('%H:%M')}"
        # Caso contrário, mostrar data completa
        return dt.strftime("%d/%m/%Y às %H:%M")
    except Exception:
        return timestamp_str


def show_history_sidebar(
    firebase_service=None,
    limit: int = 10,
    show_title: bool = True
) -> None:
    """
    Exibe o histórico de ações na barra lateral.

    Args:
        firebase_service: Serviço do Firebase (opcional)
        limit: Número máximo de entradas para exibir
        show_title: Se deve mostrar o título da seção
    """
    try:
        # Inicializar serviço de histórico
        history_service = HistoryService(firebase_service)

        # Título da seção
        if show_title:
            st.sidebar.subheader("📜 Histórico de Ações")

        # Controles
        cols = st.sidebar.columns([4, 1])
        with cols[0]:
            filter_type = st.selectbox(
                "Filtrar por:",
                options=[
                    "Todos",
                    "Geração de Planos",
                    "Criação de Tarefas"
                ],
                index=0
            )

        with cols[1]:
            if st.button("🗑️", help="Limpar histórico"):
                if history_service.clear_history():
                    st.sidebar.success("Histórico limpo!")
                    st.rerun()

        # Mapear opção para tipo de ação
        action_filter = None
        if filter_type == "Geração de Planos":
            action_filter = "plan_generation"
        elif filter_type == "Criação de Tarefas":
            action_filter = "task_creation"

        # Obter histórico
        history_entries = history_service.get_history(
            limit=limit,
            action_type=action_filter
        )

        # Verificar se há entradas
        if not history_entries:
            st.sidebar.info("Nenhuma ação registrada ainda.")
            return

        # Exibir cada entrada
        for entry in history_entries:
            with st.sidebar.container():
                # Determinar ícone com base no tipo de ação
                icon = "📝"
                if entry.get("action_type") == "plan_generation":
                    icon = "🧠"
                elif entry.get("action_type") == "task_creation":
                    icon = "✅"

                # Formatação do cabeçalho
                st.caption(
                    f"{icon} {format_timestamp(entry.get('timestamp', ''))}"
                )

                # Descrição da ação
                st.markdown(f"**{entry.get('description', '')}**")

                # Detalhes adicionais (se houver)
                data = entry.get("data", {})
                if data:
                    if "has_image" in data and data["has_image"]:
                        st.caption("📷 Incluiu uma imagem")

                    if "source" in data and data["source"] != "manual":
                        st.caption(f"Fonte: {data['source']}")

                # Separador
                st.markdown("---")

    except Exception as e:
        log_error(f"Erro ao exibir histórico: {str(e)}")
        st.sidebar.error("Não foi possível carregar o histórico.")


def show_service_selector(on_change=None) -> bool:
    """
    Exibe o seletor de serviço na barra lateral.

    Args:
        on_change: Função a ser chamada quando a seleção mudar

    Returns:
        bool: True se o serviço modularizado estiver selecionado
    """
    # Seleção de serviço
    service_option = st.sidebar.radio(
        "Serviço de IA",
        options=["Modularizado", "Original"],
        index=0,
        help="Escolha qual serviço usar para análise de imagens"
    )

    # Mostrar informações sobre o serviço selecionado
    if service_option == "Modularizado":
        st.sidebar.info(
            "**Serviço Modularizado:** Implementação otimizada para análise "
            "de imagens e resposta multimodal."
        )
        use_modular = True
    else:
        st.sidebar.info(
            "**Serviço Original:** Implementação padrão de análise de imagens."
        )
        use_modular = False

    # Atualizar o estado da sessão com a escolha
    session_state_changed = (
        'use_modular_service' not in st.session_state or
        st.session_state.use_modular_service != use_modular
    )

    if session_state_changed:
        st.session_state.use_modular_service = use_modular

        # Se mudar o serviço, vamos reinicializar
        if 'image_analysis_service' in st.session_state:
            del st.session_state.image_analysis_service

        log_success(f"Serviço de IA alterado para: {service_option}")

        # Chamar callback se fornecido
        if on_change:
            on_change(use_modular)

    return use_modular
