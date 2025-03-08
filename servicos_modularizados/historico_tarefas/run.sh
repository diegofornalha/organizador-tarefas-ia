#!/bin/bash

echo "====================================================="
echo "  DEMONSTRAÇÃO DO MÓDULO DE HISTÓRICO DE TAREFAS"
echo "====================================================="
echo ""

# Diretório atual do script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Configurar PYTHONPATH
export PYTHONPATH="$DIR/../..:$PYTHONPATH"

# Verificar se o streamlit está instalado
if ! python -c "import streamlit" &> /dev/null; then
    echo "Instalando dependência: streamlit..."
    pip install streamlit pandas altair
fi

# Criar arquivo de demonstração temporário
cat > app_demo.py << 'EOF'
"""
Aplicativo de demonstração para o módulo de histórico de tarefas.
Este script mostra como utilizar o módulo historico_tarefas
de forma independente.
"""

import streamlit as st
import uuid
from datetime import datetime, timedelta

# Importar o módulo de histórico de tarefas
try:
    import historico_tarefas
except ImportError:
    import sys
    import os
    # Adicionar diretório pai ao path
    module_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if module_path not in sys.path:
        sys.path.insert(0, module_path)
    import historico_tarefas

# Configurar a página
st.set_page_config(
    page_title="Demo - Histórico de Tarefas",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo personalizado
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #f0f0f0;
        border-radius: 4px 4px 0 0;
        padding: 8px 16px;
        border: 1px solid #e0e0e0;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4CAF50;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Título principal
    st.title("📊 Demonstração: Módulo de Histórico de Tarefas")

    # Informações sobre o módulo
    st.info("""
    **Módulo: historico_tarefas**

    Este módulo fornece funcionalidades para rastrear, visualizar e analisar
    o histórico de tarefas em uma aplicação Streamlit. Ele pode ser facilmente
    integrado a qualquer aplicação que precise manter um registro de atividades
    relacionadas a tarefas.
    """)

    # Dividir em abas
    tab1, tab2, tab3 = st.tabs([
        "✨ Criação de Tarefas",
        "📋 Visualização do Histórico",
        "📊 Análises"
    ])

    # Tab 1: Criar tarefas de exemplo
    with tab1:
        st.header("Criação de Tarefas de Exemplo")

        # Formulário para criar tarefa
        with st.form("criar_tarefa"):
            st.subheader("Nova Tarefa")

            # Campos do formulário
            titulo = st.text_input("Título da tarefa", value="Tarefa de exemplo")
            descricao = st.text_area("Descrição", value="Descrição da tarefa de exemplo")
            prioridade = st.select_slider(
                "Prioridade",
                options=["Baixa", "Média", "Alta"],
                value="Média"
            )
            data_vencimento = st.date_input(
                "Data de vencimento",
                value=datetime.now() + timedelta(days=7)
            )

            # Botões
            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("Criar Tarefa")
            with col2:
                criar_varias = st.form_submit_button("Criar 5 Tarefas de Exemplo")

        # Processar criação de tarefa única
        if submit:
            task_id = str(uuid.uuid4())
            historico_tarefas.record_task_event(
                task_id=task_id,
                task_title=titulo,
                event_type="created",
                details=f"Prioridade: {prioridade}, Vencimento: {data_vencimento}"
            )
            st.success(f"Tarefa '{titulo}' criada com sucesso!")

            # Perguntar se deseja marcar como concluída
            if st.button("Marcar como Concluída"):
                historico_tarefas.record_task_event(
                    task_id=task_id,
                    task_title=titulo,
                    event_type="completed",
                    details="Tarefa concluída na demonstração"
                )
                st.success(f"Tarefa '{titulo}' marcada como concluída!")

        # Processar criação de múltiplas tarefas
        if criar_varias:
            for i in range(1, 6):
                task_id = str(uuid.uuid4())
                task_title = f"Tarefa demonstrativa #{i}"

                # Criar tarefa
                historico_tarefas.record_task_event(
                    task_id=task_id,
                    task_title=task_title,
                    event_type="created",
                    details=f"Tarefa automática criada na demonstração"
                )

                # Algumas tarefas serão concluídas
                if i % 2 == 0:
                    historico_tarefas.record_task_event(
                        task_id=task_id,
                        task_title=task_title,
                        event_type="completed",
                        details="Concluída automaticamente na demonstração"
                    )

                # Uma tarefa será excluída
                if i == 3:
                    historico_tarefas.record_task_event(
                        task_id=task_id,
                        task_title=task_title,
                        event_type="deleted",
                        details="Excluída na demonstração"
                    )

            st.success("5 tarefas demonstrativas foram criadas com sucesso!")

    # Tab 2: Visualizar histórico
    with tab2:
        st.header("Visualização do Histórico de Tarefas")

        # Exibir o componente de histórico
        historico_tarefas.show_tasks_history_panel()

    # Tab 3: Análises
    with tab3:
        st.header("Análises de Produtividade")

        # Exibir o componente de análise
        historico_tarefas.show_tasks_analytics()

    # Sidebar com resumo
    historico_tarefas.show_tasks_history_sidebar()

    # Informações sobre a implementação
    st.divider()
    st.subheader("Sobre a Implementação")

    st.markdown("""
    Este módulo implementa as seguintes funções principais:

    * `record_task_event()`: Registra eventos relacionados a tarefas
    * `get_tasks_history()`: Obtém o histórico de tarefas
    * `show_tasks_history_sidebar()`: Exibe um resumo do histórico na barra lateral
    * `show_tasks_history_panel()`: Exibe o histórico completo em um painel
    * `show_tasks_analytics()`: Exibe análises e gráficos baseados no histórico
    * `clear_tasks_history()`: Limpa o histórico de tarefas

    O módulo suporta integração com Firestore para persistência dos dados,
    quando disponível, e também mantém os dados na session_state do Streamlit.
    """)

    # Mostrar código de exemplo
    with st.expander("Ver exemplo de código de uso"):
        st.code("""
# Importar o módulo
import historico_tarefas

# Registrar evento de criação de tarefa
historico_tarefas.record_task_event(
    task_id="12345",
    task_title="Minha tarefa",
    event_type="created",
    details="Detalhes adicionais da tarefa"
)

# Exibir o histórico na sidebar
historico_tarefas.show_tasks_history_sidebar()

# Exibir painel completo
historico_tarefas.show_tasks_history_panel()

# Exibir análises
historico_tarefas.show_tasks_analytics()
        """, language="python")

if __name__ == "__main__":
    main()
EOF

# Executar a demonstração
echo "Iniciando a demonstração do módulo de histórico de tarefas..."
echo "A aplicação estará disponível em http://localhost:8513"
echo ""
echo "Pressione Ctrl+C para encerrar quando terminar."
echo "====================================================="

streamlit run app_demo.py --server.port=8513
