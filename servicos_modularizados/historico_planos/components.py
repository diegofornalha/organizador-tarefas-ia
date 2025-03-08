"""
Componentes para gerenciamento de histórico de planos.
Este módulo fornece funcionalidades para exibir, salvar e gerenciar histórico de planos
gerados em qualquer aplicativo que o utilize.
"""

import streamlit as st
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
import os
import sys
import json

# Configurações de caminhos e imports
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICES_DIR = os.path.dirname(CURRENT_DIR)
GERAL_DIR = os.path.join(SERVICES_DIR, "geral")

# Adicionar diretórios ao path se necessário
if GERAL_DIR not in sys.path:
    sys.path.insert(0, GERAL_DIR)

# Importar funcionalidades necessárias
try:
    from geral.app_logger import log_success, log_error, log_warning
    from geral.firestore_service import firestore_service
except ImportError:
    # Funções padrão para uso quando as importações falham
    def log_success(message):
        print(f"SUCCESS: {message}")

    def log_error(message):
        print(f"ERROR: {message}")

    def log_warning(message):
        print(f"WARNING: {message}")

    # Variável nula para caso o firestore não esteja disponível
    firestore_service = None


def show_plans_history_sidebar(
    on_new_query_click: Optional[Callable] = None,
    container=None,
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
    ensure_plans_history_loaded()

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
        clear_plans_history()
        ui.success("Histórico de planos limpo!")
        st.rerun()


def show_plans_history_panel(container=None):
    """
    Exibe o histórico de planos em um painel principal com opções de filtragem.

    Args:
        container: Container onde o componente será renderizado (opcional)
    """
    # Escolher onde renderizar
    ui = container if container else st

    ui.header("📚 Histórico de Planos")

    # Carregar histórico
    ensure_plans_history_loaded()

    if not st.session_state.planos_historico:
        ui.info("Nenhum plano foi gerado ainda.")
        return

    # Adicionar filtros
    col1, col2 = ui.columns([2, 1])
    with col1:
        filtro = ui.text_input("Buscar planos", placeholder="Digite para filtrar...")
    with col2:
        ordem = ui.selectbox(
            "Ordenar por", ["Mais recentes", "Mais antigos", "Alfabética"]
        )

    # Aplicar filtros e ordenação
    planos_filtrados = filtrar_planos(st.session_state.planos_historico, filtro, ordem)

    ui.write(
        f"Exibindo {len(planos_filtrados)} de {len(st.session_state.planos_historico)} planos"
    )

    # Exibir planos em formato de grade
    colunas = ui.columns(3)

    for i, plano in enumerate(planos_filtrados):
        col_idx = i % 3
        with colunas[col_idx]:
            # Card para cada plano
            st.markdown(
                f"""
                <div style="
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    padding: 10px;
                    margin-bottom: 10px;
                    background-color: #f9f9f9;
                ">
                    <h3>{plano.get('titulo', 'Plano sem título')}</h3>
                    <p>Data: {formatar_data(plano.get('data', ''))}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Botões de ação
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                if st.button("🔍 Ver Detalhes", key=f"ver_{i}"):
                    st.session_state.plano_selecionado = plano
                    st.rerun()
            with btn_col2:
                if st.button("❌ Excluir", key=f"excluir_{i}"):
                    remover_plano_do_historico(i)
                    st.success("Plano removido!")
                    st.rerun()

    # Exibir detalhes do plano selecionado
    if "plano_selecionado" in st.session_state and st.session_state.plano_selecionado:
        with ui.expander("Detalhes do Plano", expanded=True):
            plano = st.session_state.plano_selecionado
            ui.subheader(plano.get("titulo", "Plano sem título"))
            ui.caption(f"Data: {formatar_data(plano.get('data', ''))}")

            # Exibir JSON
            ui.text_area(
                "JSON do Plano",
                value=plano.get("json", "{}"),
                height=300,
                disabled=True,
            )

            # Tentar exibir tarefas de forma estruturada
            try:
                plano_data = json.loads(plano.get("json", "{}"))
                if "tarefas" in plano_data:
                    ui.subheader("Tarefas")
                    for j, tarefa in enumerate(plano_data["tarefas"]):
                        with ui.expander(f"{j+1}. {tarefa.get('titulo', 'Tarefa')}"):
                            ui.write(f"**Descrição:** {tarefa.get('descricao', 'N/A')}")
                            ui.write(
                                f"**Prioridade:** {tarefa.get('prioridade', 'N/A')}"
                            )

                            # Exibir subtarefas
                            if "subtarefas" in tarefa and tarefa["subtarefas"]:
                                ui.write("**Subtarefas:**")
                                for k, subtarefa in enumerate(tarefa["subtarefas"]):
                                    ui.write(
                                        f"- {subtarefa.get('titulo', 'Subtarefa')}"
                                    )
            except Exception as e:
                ui.warning(f"Não foi possível processar detalhes do plano: {str(e)}")

            # Botão para fechar detalhes
            if ui.button("Fechar Detalhes"):
                st.session_state.plano_selecionado = None
                st.rerun()

    # Botão para limpar histórico
    if st.session_state.planos_historico:
        if ui.button("🗑️ Limpar Todo o Histórico", type="primary"):
            clear_plans_history()
            ui.success("Histórico de planos limpo com sucesso!")
            if "plano_selecionado" in st.session_state:
                st.session_state.plano_selecionado = None
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
        ensure_plans_history_loaded()

        # Adicionar ao histórico local
        st.session_state.planos_historico.append(plan_data)

        # Salvar no Firestore também, se disponível
        if firestore_service:
            try:
                firestore_service.save_plan_to_history(plan_data)
            except Exception as e:
                log_error(f"Erro ao salvar plano no Firestore: {str(e)}")

        return True

    except Exception as e:
        log_error(f"Erro ao salvar plano no histórico: {str(e)}")
        return False


def get_plans_history(limit: int = 20) -> List[Dict[str, Any]]:
    """
    Recupera o histórico de planos.

    Args:
        limit: Número máximo de planos a retornar

    Returns:
        List[Dict]: Lista de planos do histórico
    """
    # Garantir que o histórico está carregado
    ensure_plans_history_loaded()

    # Retornar os planos, limitando pela quantidade solicitada
    return (
        st.session_state.planos_historico[:limit]
        if st.session_state.planos_historico
        else []
    )


def clear_plans_history() -> bool:
    """
    Limpa o histórico de planos (tanto da session_state quanto do Firestore).

    Returns:
        bool: True se o histórico foi limpo com sucesso
    """
    # Limpar da session_state
    st.session_state.planos_historico = []

    # Limpar do Firestore, se disponível
    if firestore_service:
        try:
            if firestore_service.clear_plans_history():
                log_success("Histórico de planos limpo também no Firestore")
        except Exception as e:
            log_error(f"Erro ao limpar histórico no Firestore: {str(e)}")

    return True


def ensure_plans_history_loaded():
    """
    Garante que o histórico de planos está carregado na session_state.
    Se não estiver, tenta carregar do Firestore.
    """
    if "planos_historico" not in st.session_state:
        st.session_state.planos_historico = []

        # Tentar carregar do Firestore, se disponível
        if firestore_service:
            try:
                planos_firestore = firestore_service.get_plans_history()
                if planos_firestore:
                    # Converter para o formato usado na session_state
                    for plano in planos_firestore:
                        st.session_state.planos_historico.append(
                            {
                                "titulo": plano.get("titulo", "Plano sem título"),
                                "json": plano.get("json", "{}"),
                                "data": plano.get(
                                    "created_at", datetime.now().isoformat()
                                ),
                            }
                        )
                    log_success(
                        f"Carregados {len(planos_firestore)} planos do histórico do Firestore"
                    )
            except Exception as e:
                log_error(f"Erro ao carregar histórico do Firestore: {str(e)}")


# Funções auxiliares


def filtrar_planos(planos, filtro, ordem):
    """
    Filtra e ordena a lista de planos conforme critérios.

    Args:
        planos: Lista de planos para filtrar
        filtro: Texto para filtrar planos pelo título
        ordem: Critério de ordenação ("Mais recentes", "Mais antigos", "Alfabética")

    Returns:
        list: Lista de planos filtrada e ordenada
    """
    # Aplicar filtro textual
    if filtro:
        planos_filtrados = []
        filtro_lower = filtro.lower()

        for plano in planos:
            # Verificar no título
            titulo = plano.get("titulo", "").lower()
            if filtro_lower in titulo:
                planos_filtrados.append(plano)
                continue

            # Verificar no conteúdo JSON
            try:
                conteudo = plano.get("json", "{}").lower()
                if filtro_lower in conteudo:
                    planos_filtrados.append(plano)
            except:
                pass
    else:
        planos_filtrados = planos.copy()

    # Aplicar ordenação
    if ordem == "Mais recentes":
        planos_filtrados.sort(key=lambda x: x.get("data", ""), reverse=True)
    elif ordem == "Mais antigos":
        planos_filtrados.sort(key=lambda x: x.get("data", "") or "")
    elif ordem == "Alfabética":
        planos_filtrados.sort(key=lambda x: x.get("titulo", "").lower())

    return planos_filtrados


def formatar_data(data_str):
    """
    Formata uma data ISO para exibição amigável.

    Args:
        data_str: String de data em formato ISO

    Returns:
        str: Data formatada
    """
    try:
        if not data_str:
            return "Data desconhecida"

        # Se for uma data no formato ISO
        if "T" in data_str:
            data_obj = datetime.fromisoformat(data_str)
            return data_obj.strftime("%d/%m/%Y %H:%M")

        # Se for apenas uma data
        return data_str
    except:
        return data_str


def remover_plano_do_historico(indice):
    """
    Remove um plano específico do histórico pelo seu índice.

    Args:
        indice: Índice do plano na lista

    Returns:
        bool: True se o plano foi removido com sucesso
    """
    if "planos_historico" not in st.session_state or indice >= len(
        st.session_state.planos_historico
    ):
        return False

    # Obter o plano antes de removê-lo
    plano = st.session_state.planos_historico[indice]

    # Remover da session_state
    st.session_state.planos_historico.pop(indice)

    # Tentar remover do Firestore, se disponível
    if firestore_service and "id" in plano:
        try:
            # Tentar excluir o documento
            firestore_service.delete_document("planos_historico", plano["id"])
        except Exception as e:
            log_error(f"Erro ao excluir plano do Firestore: {str(e)}")

    return True
