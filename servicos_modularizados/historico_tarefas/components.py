"""
Componentes para gerenciamento de histórico de tarefas.
Este módulo fornece funcionalidades para rastrear e visualizar
o histórico de criação, conclusão e remoção de tarefas.
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import os
import sys
import json
import uuid
import pandas as pd
import altair as alt
import calendar
import locale

# Tentar configurar o locale para português
try:
    locale.setlocale(locale.LC_ALL, "pt_BR.UTF-8")
except:
    try:
        locale.setlocale(locale.LC_ALL, "Portuguese_Brazil")
    except:
        pass  # Fallback para o locale padrão

# Configurações de caminhos e imports
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICES_DIR = os.path.dirname(CURRENT_DIR)
GERAL_DIR = os.path.join(SERVICES_DIR, "geral")

# Adicionar diretórios ao path se necessário
if GERAL_DIR not in sys.path:
    sys.path.insert(0, GERAL_DIR)

# Verificar se estamos sendo executados como componente importado
# e não tentar configurar a página neste caso
IS_IMPORTED = not getattr(st, "_is_running_with_streamlit", False)

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


# Tipos de eventos
TASK_CREATED = "created"
TASK_COMPLETED = "completed"
TASK_REOPENED = "reopened"
TASK_DELETED = "deleted"
SUBTASK_COMPLETED = "subtask_completed"
SUBTASK_REOPENED = "subtask_reopened"


def show_tasks_history_sidebar(container=None):
    """
    Exibe um resumo do histórico de tarefas na barra lateral.

    Args:
        container: Container onde o componente será renderizado (opcional)
    """
    # Escolher onde renderizar
    ui = container if container else st.sidebar

    ui.header("📊 Histórico de Tarefas")

    # Obter histórico
    historico = get_tasks_history()

    if not historico:
        ui.info("Nenhum registro de tarefas encontrado.")
        return

    # Contadores
    eventos_por_tipo = {}
    for evento in historico:
        tipo = evento.get("type", "unknown")
        if tipo not in eventos_por_tipo:
            eventos_por_tipo[tipo] = 0
        eventos_por_tipo[tipo] += 1

    # Exibir resumo
    ui.subheader("Resumo de Atividades")

    col1, col2 = ui.columns(2)
    with col1:
        ui.metric("Total de Eventos", len(historico))
    with col2:
        ui.metric("Tarefas Criadas", eventos_por_tipo.get(TASK_CREATED, 0))

    col1, col2 = ui.columns(2)
    with col1:
        ui.metric("Tarefas Concluídas", eventos_por_tipo.get(TASK_COMPLETED, 0))
    with col2:
        ui.metric("Tarefas Excluídas", eventos_por_tipo.get(TASK_DELETED, 0))

    # Eventos recentes
    ui.subheader("Atividades Recentes")
    for evento in historico[:5]:  # Mostrar apenas os 5 mais recentes
        timestamp = evento.get("timestamp", "")
        data = datetime.fromisoformat(timestamp) if timestamp else datetime.now()
        data_formatada = data.strftime("%d/%m/%Y %H:%M")

        tipo = evento.get("type", "")
        task_title = evento.get("task_title", "Tarefa sem título")

        if tipo == TASK_CREATED:
            ui.markdown(f"✨ **{task_title}** criada em {data_formatada}")
        elif tipo == TASK_COMPLETED:
            ui.markdown(f"✅ **{task_title}** concluída em {data_formatada}")
        elif tipo == TASK_REOPENED:
            ui.markdown(f"🔄 **{task_title}** reaberta em {data_formatada}")
        elif tipo == TASK_DELETED:
            ui.markdown(f"🗑️ **{task_title}** excluída em {data_formatada}")

    # Botão para ver análise completa
    if ui.button("Ver Análise Completa"):
        st.session_state.show_tasks_analytics = True
        ui.rerun()


def show_tasks_history_panel(container=None):
    """
    Exibe o histórico completo de atividades de tarefas.

    Args:
        container: Container onde o componente será renderizado (opcional)
    """
    # Escolher onde renderizar
    ui = container if container else st

    ui.header("📋 Histórico Completo de Tarefas")

    # Obter histórico
    historico = get_tasks_history()

    if not historico:
        ui.info("Nenhum registro de tarefas encontrado.")
        return

    # Filtros
    col1, col2, col3 = ui.columns([2, 1, 1])
    with col1:
        filtro = ui.text_input("Buscar tarefas", placeholder="Digite para filtrar...")
    with col2:
        tipo_filtro = ui.selectbox(
            "Tipo de evento",
            ["Todos", "Criação", "Conclusão", "Reabertura", "Exclusão"],
        )
    with col3:
        periodo = ui.selectbox(
            "Período", ["Todos", "Hoje", "Última Semana", "Último Mês"]
        )

    # Aplicar filtros
    historico_filtrado = filtrar_historico(historico, filtro, tipo_filtro, periodo)

    ui.write(f"Exibindo {len(historico_filtrado)} de {len(historico)} registros")

    # Exibir tabela de eventos
    if historico_filtrado:
        # Converter para DataFrame para exibição
        dados = []
        for evento in historico_filtrado:
            # Data formatada
            timestamp = evento.get("timestamp", "")
            data = datetime.fromisoformat(timestamp) if timestamp else datetime.now()
            data_formatada = data.strftime("%d/%m/%Y %H:%M")

            # Tipo formatado
            tipo = evento.get("type", "")
            if tipo == TASK_CREATED:
                tipo_formatado = "Criação"
                icone = "✨"
            elif tipo == TASK_COMPLETED:
                tipo_formatado = "Conclusão"
                icone = "✅"
            elif tipo == TASK_REOPENED:
                tipo_formatado = "Reabertura"
                icone = "🔄"
            elif tipo == TASK_DELETED:
                tipo_formatado = "Exclusão"
                icone = "🗑️"
            elif tipo == SUBTASK_COMPLETED:
                tipo_formatado = "Subtarefa Concluída"
                icone = "✓"
            elif tipo == SUBTASK_REOPENED:
                tipo_formatado = "Subtarefa Reaberta"
                icone = "↻"
            else:
                tipo_formatado = tipo
                icone = "❓"

            # Adicionar linha
            dados.append(
                {
                    "Data": data_formatada,
                    "Tipo": f"{icone} {tipo_formatado}",
                    "Tarefa": evento.get("task_title", ""),
                    "Detalhes": evento.get("details", ""),
                    "ID": evento.get("id", ""),
                }
            )

        # Criar DataFrame
        if dados:
            df = pd.DataFrame(dados)
            ui.dataframe(df, hide_index=True)

    # Botão para limpar histórico
    if ui.button("Limpar Histórico de Tarefas"):
        if clear_tasks_history():
            ui.success("Histórico de tarefas limpo com sucesso!")
            ui.rerun()


def show_tasks_analytics(container=None):
    """
    Exibe análises e gráficos sobre o histórico de tarefas.

    Args:
        container: Container onde o componente será renderizado (opcional)
    """
    # Escolher onde renderizar
    ui = container if container else st

    ui.header("📊 Análise de Produtividade")

    # Obter histórico
    historico = get_tasks_history()

    if not historico:
        ui.info("Nenhum registro de tarefas encontrado para análise.")
        return

    # Preparar dados para análise
    atividades_por_dia, atividades_por_semana, atividades_por_tarefa = (
        preparar_dados_analise(historico)
    )

    # Dividir em abas
    tab1, tab2, tab3 = ui.tabs(
        ["Visão Geral", "Tarefas por Período", "Tarefas Mais Ativas"]
    )

    with tab1:
        # Métricas principais
        metricas_principais(ui, historico)

        # Gráfico geral de atividades
        ui.subheader("Distribuição de Atividades")
        eventos_por_tipo = contagem_eventos_por_tipo(historico)

        # Criar dataframe para o gráfico
        df_tipos = pd.DataFrame(
            {
                "Tipo": [
                    formatar_tipo_evento(tipo) for tipo in eventos_por_tipo.keys()
                ],
                "Quantidade": list(eventos_por_tipo.values()),
            }
        )

        # Gráfico de barras
        grafico = (
            alt.Chart(df_tipos)
            .mark_bar()
            .encode(
                x=alt.X("Tipo:N", sort="-y", axis=alt.Axis(labelAngle=0)),
                y="Quantidade:Q",
                color=alt.Color("Tipo:N", legend=None),
                tooltip=["Tipo", "Quantidade"],
            )
            .properties(height=300)
        )

        ui.altair_chart(grafico, use_container_width=True)

    with tab2:
        # Atividades por dia
        ui.subheader("Atividades por Dia")
        if atividades_por_dia:
            df_dias = pd.DataFrame(
                list(atividades_por_dia.items()), columns=["Data", "Quantidade"]
            )
            df_dias["Data"] = pd.to_datetime(df_dias["Data"])
            df_dias = df_dias.sort_values("Data")

            grafico_dias = (
                alt.Chart(df_dias)
                .mark_line(point=True)
                .encode(
                    x="Data:T", y="Quantidade:Q", tooltip=["Data:T", "Quantidade:Q"]
                )
                .properties(height=300)
            )

            ui.altair_chart(grafico_dias, use_container_width=True)
        else:
            ui.info("Dados insuficientes para gráfico de atividades diárias.")

        # Atividades por semana
        ui.subheader("Atividades por Semana")
        if atividades_por_semana:
            df_semanas = pd.DataFrame(
                list(atividades_por_semana.items()), columns=["Semana", "Quantidade"]
            )

            grafico_semanas = (
                alt.Chart(df_semanas)
                .mark_bar()
                .encode(
                    x="Semana:N",
                    y="Quantidade:Q",
                    color=alt.Color("Quantidade:Q", scale=alt.Scale(scheme="blues")),
                    tooltip=["Semana:N", "Quantidade:Q"],
                )
                .properties(height=300)
            )

            ui.altair_chart(grafico_semanas, use_container_width=True)
        else:
            ui.info("Dados insuficientes para gráfico de atividades semanais.")

    with tab3:
        # Tarefas mais ativas
        ui.subheader("Tarefas com Mais Atividades")
        if atividades_por_tarefa:
            # Ordenar por quantidade de atividades
            tarefas_ordenadas = sorted(
                atividades_por_tarefa.items(), key=lambda x: x[1]["total"], reverse=True
            )

            # Converter para DataFrame
            dados_tarefas = []
            for tarefa, contagens in tarefas_ordenadas[:10]:  # Top 10
                dados_tarefas.append(
                    {
                        "Tarefa": tarefa,
                        "Total": contagens["total"],
                        "Criação": contagens.get(TASK_CREATED, 0),
                        "Conclusão": contagens.get(TASK_COMPLETED, 0),
                        "Reabertura": contagens.get(TASK_REOPENED, 0),
                        "Exclusão": contagens.get(TASK_DELETED, 0),
                    }
                )

            df_tarefas = pd.DataFrame(dados_tarefas)

            # Gráfico de barras horizontais para as tarefas
            grafico_tarefas = (
                alt.Chart(df_tarefas)
                .mark_bar()
                .encode(
                    y=alt.Y("Tarefa:N", sort="-x"),
                    x="Total:Q",
                    color=alt.Color("Total:Q", scale=alt.Scale(scheme="reds")),
                    tooltip=[
                        "Tarefa",
                        "Total",
                        "Criação",
                        "Conclusão",
                        "Reabertura",
                        "Exclusão",
                    ],
                )
                .properties(height=min(400, len(dados_tarefas) * 40))
            )

            ui.altair_chart(grafico_tarefas, use_container_width=True)

            # Mostrar tabela com mais detalhes
            ui.dataframe(df_tarefas, hide_index=True)
        else:
            ui.info("Dados insuficientes para análise de tarefas mais ativas.")


def record_task_event(
    task_id: str, task_title: str, event_type: str, details: str = ""
) -> bool:
    """
    Registra um evento relacionado a uma tarefa.

    Args:
        task_id: ID da tarefa
        task_title: Título da tarefa
        event_type: Tipo de evento (created, completed, etc.)
        details: Detalhes adicionais do evento

    Returns:
        bool: True se o evento foi registrado com sucesso
    """
    # Garantir que o histórico existe na session_state
    if "tasks_history" not in st.session_state:
        st.session_state.tasks_history = []

    # Criar registro de evento
    evento = {
        "id": str(uuid.uuid4()),
        "task_id": task_id,
        "task_title": task_title,
        "type": event_type,
        "details": details,
        "timestamp": datetime.now().isoformat(),
    }

    # Adicionar ao histórico local
    st.session_state.tasks_history.append(evento)

    # Persistir no Firestore se disponível
    if firestore_service:
        try:
            firestore_service.add_document("tarefas_historico", evento)
        except Exception as e:
            log_error(f"Erro ao salvar evento no Firestore: {str(e)}")

    return True


def get_tasks_history() -> List[Dict[str, Any]]:
    """
    Obtém o histórico de eventos de tarefas.

    Returns:
        List[Dict]: Lista de eventos de tarefas
    """
    # Garantir que o histórico existe na session_state
    if "tasks_history" not in st.session_state:
        st.session_state.tasks_history = []

        # Tentar carregar do Firestore se disponível
        if firestore_service:
            try:
                eventos = firestore_service.get_documents("tarefas_historico")
                if eventos:
                    # Ordenar por timestamp (mais recente primeiro)
                    eventos.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
                    st.session_state.tasks_history = eventos
            except Exception as e:
                log_error(
                    f"Erro ao carregar histórico de tarefas do Firestore: {str(e)}"
                )

    # Retornar histórico ordenado
    historico = st.session_state.tasks_history
    historico.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

    return historico


def clear_tasks_history() -> bool:
    """
    Limpa o histórico de eventos de tarefas.

    Returns:
        bool: True se o histórico foi limpo com sucesso
    """
    # Limpar da session_state
    st.session_state.tasks_history = []

    # Limpar do Firestore se disponível
    if firestore_service:
        try:
            # Obter todos os eventos
            eventos = firestore_service.get_documents("tarefas_historico")

            # Excluir cada evento
            for evento in eventos:
                firestore_service.delete_document("tarefas_historico", evento.get("id"))

            log_success("Histórico de tarefas limpo do Firestore")
            return True
        except Exception as e:
            log_error(f"Erro ao limpar histórico de tarefas do Firestore: {str(e)}")
            return False

    return True


# Funções auxiliares


def filtrar_historico(historico, filtro_texto, tipo_filtro, periodo):
    """
    Filtra o histórico de eventos com base nos critérios especificados.
    """
    # Data atual
    hoje = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # Converter período para datas
    if periodo == "Hoje":
        data_inicio = hoje
    elif periodo == "Última Semana":
        data_inicio = hoje - timedelta(days=7)
    elif periodo == "Último Mês":
        data_inicio = hoje - timedelta(days=30)
    else:  # "Todos"
        data_inicio = None

    # Converter tipo_filtro para o tipo de evento
    if tipo_filtro == "Criação":
        tipo_evento = TASK_CREATED
    elif tipo_filtro == "Conclusão":
        tipo_evento = TASK_COMPLETED
    elif tipo_filtro == "Reabertura":
        tipo_evento = TASK_REOPENED
    elif tipo_filtro == "Exclusão":
        tipo_evento = TASK_DELETED
    else:  # "Todos"
        tipo_evento = None

    # Aplicar filtros
    resultado = []
    for evento in historico:
        # Filtrar por texto
        if filtro_texto:
            titulo = evento.get("task_title", "").lower()
            detalhes = evento.get("details", "").lower()
            if (
                filtro_texto.lower() not in titulo
                and filtro_texto.lower() not in detalhes
            ):
                continue

        # Filtrar por tipo
        if tipo_evento and evento.get("type") != tipo_evento:
            continue

        # Filtrar por período
        if data_inicio:
            timestamp = evento.get("timestamp", "")
            if not timestamp:
                continue

            data_evento = datetime.fromisoformat(timestamp)
            if data_evento < data_inicio:
                continue

        # Passou em todos os filtros
        resultado.append(evento)

    return resultado


def preparar_dados_analise(historico):
    """
    Prepara os dados para análise.
    """
    # Atividades por dia
    atividades_por_dia = {}

    # Atividades por semana
    atividades_por_semana = {}

    # Atividades por tarefa
    atividades_por_tarefa = {}

    for evento in historico:
        # Extrair data
        timestamp = evento.get("timestamp", "")
        if not timestamp:
            continue

        data_evento = datetime.fromisoformat(timestamp)

        # Formatar data (apenas ano-mês-dia)
        data_str = data_evento.strftime("%Y-%m-%d")

        # Contar para atividades por dia
        if data_str not in atividades_por_dia:
            atividades_por_dia[data_str] = 0
        atividades_por_dia[data_str] += 1

        # Formatar semana (ano-semana)
        semana_str = f"{data_evento.year}-W{data_evento.isocalendar()[1]}"

        # Contar para atividades por semana
        if semana_str not in atividades_por_semana:
            atividades_por_semana[semana_str] = 0
        atividades_por_semana[semana_str] += 1

        # Obter tarefa
        tarefa = evento.get("task_title", "")
        tipo = evento.get("type", "")

        # Contar para atividades por tarefa
        if tarefa not in atividades_por_tarefa:
            atividades_por_tarefa[tarefa] = {"total": 0}

        # Incrementar contagens
        atividades_por_tarefa[tarefa]["total"] += 1

        if tipo not in atividades_por_tarefa[tarefa]:
            atividades_por_tarefa[tarefa][tipo] = 0
        atividades_por_tarefa[tarefa][tipo] += 1

    return atividades_por_dia, atividades_por_semana, atividades_por_tarefa


def metricas_principais(ui, historico):
    """
    Exibe as métricas principais de produtividade.
    """
    # Calcular métricas
    total_eventos = len(historico)

    # Contagem por tipo
    eventos_por_tipo = contagem_eventos_por_tipo(historico)

    # Exibir métricas em cards
    col1, col2, col3 = ui.columns(3)

    with col1:
        ui.metric("Total de Atividades", total_eventos)

    with col2:
        tarefas_criadas = eventos_por_tipo.get(TASK_CREATED, 0)
        tarefas_concluidas = eventos_por_tipo.get(TASK_COMPLETED, 0)

        # Taxa de conclusão (se houver tarefas criadas)
        if tarefas_criadas > 0:
            taxa_conclusao = (tarefas_concluidas / tarefas_criadas) * 100
            ui.metric(
                "Taxa de Conclusão",
                f"{taxa_conclusao:.1f}%",
                f"{tarefas_concluidas}/{tarefas_criadas} tarefas",
            )
        else:
            ui.metric("Taxa de Conclusão", "N/A")

    with col3:
        # Atividade na última semana
        hoje = datetime.now()
        uma_semana_atras = hoje - timedelta(days=7)

        atividades_recentes = 0
        for evento in historico:
            timestamp = evento.get("timestamp", "")
            if not timestamp:
                continue

            data_evento = datetime.fromisoformat(timestamp)
            if data_evento >= uma_semana_atras:
                atividades_recentes += 1

        ui.metric("Atividades (7 dias)", atividades_recentes)


def contagem_eventos_por_tipo(historico):
    """
    Conta eventos por tipo.
    """
    contagem = {}
    for evento in historico:
        tipo = evento.get("type", "unknown")
        if tipo not in contagem:
            contagem[tipo] = 0
        contagem[tipo] += 1

    return contagem


def formatar_tipo_evento(tipo):
    """
    Formata o tipo de evento para exibição.
    """
    if tipo == TASK_CREATED:
        return "Criação"
    elif tipo == TASK_COMPLETED:
        return "Conclusão"
    elif tipo == TASK_REOPENED:
        return "Reabertura"
    elif tipo == TASK_DELETED:
        return "Exclusão"
    elif tipo == SUBTASK_COMPLETED:
        return "Subtarefa Concluída"
    elif tipo == SUBTASK_REOPENED:
        return "Subtarefa Reaberta"
    else:
        return tipo
