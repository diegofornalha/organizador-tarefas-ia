"""
Aplicação de demonstração do módulo de histórico de planos.
"""

import streamlit as st
import json
from datetime import datetime
from historico_planos import (
    show_plans_history_sidebar,
    show_plans_history_panel,
    save_plan_to_history,
)

# Configurar página apenas quando este script é executado diretamente
if __name__ == "__main__":
    st.set_page_config(
        page_title="Demo de Histórico de Planos", page_icon="📚", layout="wide"
    )

# Título da página
st.title("📚 Demonstração do Histórico de Planos")

# Exibir o histórico na barra lateral
show_plans_history_sidebar()

# Conteúdo principal - Dividir em abas
tab1, tab2 = st.tabs(["✨ Criar Plano de Exemplo", "📋 Visualizar Histórico Completo"])

# Aba 1: Criar plano de exemplo
with tab1:
    st.header("Criar um Plano de Exemplo")

    # Formulário para criar um plano de exemplo
    titulo = st.text_input("Título do Plano", "Plano de Exemplo")
    descricao = st.text_area(
        "Descrição",
        "Este é um plano de exemplo criado para testar o módulo de histórico.",
    )

    # Criar estrutura de tarefas de exemplo
    tarefas = [
        {
            "titulo": "Tarefa de exemplo 1",
            "descricao": "Descrição da tarefa 1",
            "prioridade": "alta",
            "subtarefas": [
                {"titulo": "Subtarefa 1.1", "descricao": "Descrição da subtarefa 1.1"},
                {"titulo": "Subtarefa 1.2", "descricao": "Descrição da subtarefa 1.2"},
            ],
        },
        {
            "titulo": "Tarefa de exemplo 2",
            "descricao": "Descrição da tarefa 2",
            "prioridade": "média",
            "subtarefas": [
                {"titulo": "Subtarefa 2.1", "descricao": "Descrição da subtarefa 2.1"}
            ],
        },
    ]

    # Construir o plano completo
    plano = {"titulo": titulo, "descricao": descricao, "tarefas": tarefas}

    # Exibir o JSON do plano
    with st.expander("Visualizar JSON do plano"):
        st.code(json.dumps(plano, indent=2), language="json")

    # Botão para salvar no histórico
    if st.button("Salvar Plano no Histórico"):
        plano_info = {
            "titulo": plano["titulo"],
            "json": json.dumps(plano),
            "data": datetime.now().isoformat(),
        }

        if save_plan_to_history(plano_info):
            st.success(f"Plano '{plano['titulo']}' salvo no histórico!")
            st.rerun()
        else:
            st.error("Erro ao salvar plano no histórico")

# Aba 2: Visualizar histórico completo
with tab2:
    # Utilizar o novo componente de visualização em painel
    show_plans_history_panel()

# Informações sobre o módulo
with st.expander("Sobre este módulo"):
    st.write(
        """
    O módulo **Histórico de Planos** é uma biblioteca independente para gerenciar o histórico
    de planos gerados em qualquer aplicativo. Ele oferece:

    1. **Visualização**: Componentes para exibir o histórico na barra lateral e em painel completo
    2. **Persistência**: Salva tanto na sessão quanto no Firestore (se disponível)
    3. **Interação**: Permite consultar, filtrar, visualizar, exportar e limpar o histórico

    Este módulo foi projetado para ser reutilizável e pode ser incorporado em qualquer
    aplicativo Streamlit que precise gerenciar histórico de planos.
    """
    )

    # Exemplos de código de uso
    with st.expander("Exemplos de código"):
        st.code(
            """
# Importar o módulo
from historico_planos import (
    show_plans_history_sidebar,
    show_plans_history_panel,
    save_plan_to_history,
    get_plans_history,
    clear_plans_history
)

# Exibir na barra lateral
show_plans_history_sidebar()

# Exibir em painel principal (com filtros e visualização detalhada)
show_plans_history_panel()

# Salvar um novo plano
plano_info = {
    "titulo": "Meu Plano",
    "json": json.dumps(dados_do_plano),
    "data": datetime.now().isoformat()
}
save_plan_to_history(plano_info)

# Obter a lista de planos programaticamente
planos = get_plans_history()

# Limpar o histórico
clear_plans_history()
""",
            language="python",
        )
