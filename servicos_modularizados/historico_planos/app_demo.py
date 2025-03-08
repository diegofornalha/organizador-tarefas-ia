"""
Aplicação de demonstração do módulo de histórico de planos.
"""

import streamlit as st
import json
from datetime import datetime

# Configurar página APENAS quando este script é executado diretamente
# Esta DEVE ser a primeira chamada Streamlit
if __name__ == "__main__":
    st.set_page_config(
        page_title="Demo de Histórico de Planos", page_icon="📚", layout="wide"
    )

    # Definir flag para indicar que estamos executando com o Streamlit
    setattr(st, "_is_running_with_streamlit", True)

# Importar os componentes APÓS a configuração
try:
    from historico_planos import (
        show_plans_history_sidebar,
        show_plans_history_panel,
        save_plan_to_history,
    )
except ImportError:
    import sys
    import os

    # Adicionar diretório pai ao path
    module_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if module_path not in sys.path:
        sys.path.insert(0, module_path)
    from historico_planos import (
        show_plans_history_sidebar,
        show_plans_history_panel,
        save_plan_to_history,
    )

# Título da página
st.title("📚 Demonstração do Histórico de Planos")

# Exibir o histórico na barra lateral
show_plans_history_sidebar()

# Conteúdo principal - Dividir em abas
tab1, tab2 = st.tabs(["✨ Criar Plano de Exemplo", "📋 Visualizar Histórico Completo"])

# Aba 1: Criar plano de exemplo
with tab1:
    st.header("Criar Plano de Exemplo")

    # Formulário para criar plano
    with st.form("create_plan_form"):
        # Dados do plano
        plan_title = st.text_input("Título do Plano", value="Meu Plano de Exemplo")
        plan_description = st.text_area(
            "Descrição do Plano",
            value="Este é um plano de exemplo criado para demonstrar o funcionamento do histórico.",
        )

        # Etapas do plano
        st.subheader("Etapas do Plano")
        steps = []

        # Adicionar algumas etapas de exemplo
        for i in range(1, 4):
            step_title = st.text_input(f"Etapa {i}", value=f"Etapa {i} de exemplo")
            step_description = st.text_area(
                f"Descrição da Etapa {i}",
                value=f"Descrição da etapa {i} do plano de exemplo",
            )
            steps.append({"title": step_title, "description": step_description})

        # Botão para salvar
        submitted = st.form_submit_button("Salvar Plano no Histórico")

    # Processar o envio do formulário
    if submitted:
        # Criar dados do plano
        plan_data = {
            "title": plan_title,
            "description": plan_description,
            "steps": steps,
            "created_at": datetime.now().isoformat(),
            "source": "app_demo",
        }

        # Salvar no histórico
        success = save_plan_to_history(plan_data)

        if success:
            st.success("✅ Plano salvo com sucesso no histórico!")
        else:
            st.error("❌ Erro ao salvar o plano no histórico")

# Aba 2: Visualizar histórico completo
with tab2:
    show_plans_history_panel()

# Exemplo de código
with st.expander("Ver código de exemplo de uso"):
    st.code(
        """
# Importar os componentes necessários
from historico_planos import (
    show_plans_history_sidebar,
    show_plans_history_panel,
    save_plan_to_history
)

# Exibir histórico na barra lateral
show_plans_history_sidebar()

# Exibir painel completo em qualquer container
show_plans_history_panel()

# Salvar um plano no histórico
plan_data = {
    "title": "Meu Plano",
    "description": "Descrição do plano",
    "steps": [
        {"title": "Etapa 1", "description": "Fazer algo"},
        {"title": "Etapa 2", "description": "Fazer outra coisa"}
    ],
    "created_at": "2023-07-15T10:30:00"
}
save_plan_to_history(plan_data)
""",
        language="python",
    )

if __name__ == "__main__":
    # Não precisamos usar main() aqui pois o código já está estruturado
    pass
