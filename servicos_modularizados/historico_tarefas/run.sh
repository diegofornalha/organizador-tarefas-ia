#!/bin/bash

echo "====================================================="
echo "  DEMONSTRAÇÃO DO MÓDULO DE HISTÓRICO DE TAREFAS"
echo "====================================================="
echo ""

# Diretório atual do script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Configurar PYTHONPATH para incluir diretórios necessários
PARENT_DIR="$(dirname "$(pwd)")"
ROOT_DIR="$(dirname "$PARENT_DIR")"
GERAL_DIR="$PARENT_DIR/geral"

export PYTHONPATH="$ROOT_DIR:$PARENT_DIR:$DIR:$GERAL_DIR:$PYTHONPATH"
echo "PYTHONPATH configurado: $PYTHONPATH"

# Verificar se o streamlit está instalado
if ! python -c "import streamlit" &> /dev/null; then
    echo "Instalando dependência: streamlit..."
    pip install streamlit pandas altair
fi

# Verificar conflitos de porta
if lsof -i :8513 | grep LISTEN > /dev/null; then
    echo "AVISO: A porta 8513 já está em uso. Outro serviço pode estar rodando na mesma porta."
    echo "Pressione Ctrl+C para cancelar ou ENTER para tentar iniciar mesmo assim."
    read
fi

# Reinstanciar a aplicação demo temporária
cat > app_demo.py << 'EOF'
"""
Aplicativo de demonstração para o módulo de histórico de tarefas.
Este script mostra como utilizar o módulo historico_tarefas
de forma independente.
"""

import streamlit as st
import uuid
from datetime import datetime, timedelta

# Configurar a página APENAS quando este script é executado diretamente
# DEVE ser a primeira chamada Streamlit no aplicativo
if __name__ == "__main__":
    st.set_page_config(
        page_title="Demo - Histórico de Tarefas",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Definir flag para indicar que estamos executando com o Streamlit
    setattr(st, "_is_running_with_streamlit", True)

# Importar o módulo de histórico de tarefas - APÓS a configuração
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

def main():
    st.title("📊 Demonstração do Histórico de Tarefas")
    st.write("Este aplicativo demonstra as funcionalidades do módulo de histórico de tarefas.")

    # Exibir histórico na barra lateral
    historico_tarefas.show_tasks_history_sidebar()

    # Dividir a interface em abas
    tab1, tab2, tab3 = st.tabs([
        "✨ Registrar Eventos",
        "📋 Histórico Completo",
        "📊 Análises"
    ])

    # Aba 1: Registrar eventos de exemplo
    with tab1:
        st.header("Registrar Eventos de Tarefas")
        st.write("Use este formulário para registrar eventos de exemplo no histórico.")

        col1, col2 = st.columns(2)
        with col1:
            task_id = st.text_input("ID da Tarefa", value=str(uuid.uuid4())[:8])
            task_title = st.text_input("Título da Tarefa", value="Exemplo de tarefa")

        with col2:
            # Mapear os tipos de evento em português para inglês
            tipo_evento_opcoes = {
                "Criada": "created",
                "Concluída": "completed",
                "Atualizada": "updated",
                "Excluída": "deleted",
                "Arquivada": "archived"
            }

            tipo_evento_exibicao = st.selectbox(
                "Tipo de Evento",
                options=list(tipo_evento_opcoes.keys())
            )
            # Converter o tipo selecionado para o valor em inglês
            event_type = tipo_evento_opcoes[tipo_evento_exibicao]

            details = st.text_area("Detalhes", value="Detalhes sobre o evento da tarefa")

        if st.button("Registrar Evento de Tarefa"):
            success = historico_tarefas.record_task_event(
                task_id=task_id,
                task_title=task_title,
                event_type=event_type,
                details=details
            )

            if success:
                st.success(f"Evento '{tipo_evento_exibicao}' registrado com sucesso!")
            else:
                st.error("Erro ao registrar evento. Verifique o console para mais detalhes.")

    # Aba 2: Visualizar histórico completo
    with tab2:
        historico_tarefas.show_tasks_history_panel()

    # Aba 3: Análises
    with tab3:
        historico_tarefas.show_tasks_analytics()

    # Exibir exemplo de código
    with st.expander("Ver exemplo de código de uso"):
        st.code("""
# Importar o módulo
import historico_tarefas

# Registrar evento de criação de tarefa
historico_tarefas.record_task_event(
    task_id="12345",
    task_title="Minha tarefa",
    event_type="created",  # Usar "created" para criar, "completed" para concluir, etc.
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
