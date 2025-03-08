"""
Módulo para gerenciamento de histórico de planos.
Este módulo oferece componentes para exibir, salvar e gerenciar histórico de planos
gerados em qualquer aplicativo que o utilize.
"""

# Exportar as funções e classes principais
from .components import (
    show_plans_history_sidebar,
    show_plans_history_panel,
    save_plan_to_history,
    get_plans_history,
    clear_plans_history,
)
