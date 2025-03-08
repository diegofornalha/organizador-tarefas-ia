"""
Pacote central 'geral' - Orquestrador do sistema.

Este módulo funciona como um hub central que:
1. Importa e integra serviços de outros módulos
2. Fornece interfaces unificadas para esses serviços
3. Disponibiliza componentes compartilhados
4. Orquestra a interação entre os módulos

Para usar o orquestrador:
    from geral import orquestrador

    # Carregar um módulo específico
    orquestrador.load_module('plano_tarefas')

    # Obter um componente de um módulo
    componente = orquestrador.get_component('plano_tarefas', 'nome_do_componente')
"""

# Exportar classes e funções principais do módulo geral
from .app_logger import (
    add_log,
    log_success,
    log_error,
    log_warning,
    log_debug,
    get_logs,
    clear_logs,
)
from .image_analysis_service import ImageAnalysisService
from .history_service import HistoryService
from .sidebar_components import show_history_sidebar, show_service_selector
from .firestore_service import FirestoreService, firestore_service
from .planos_history_component import show_plans_history_sidebar, save_plan_to_history

# Importar o sistema de orquestração
from .module_registry import (
    module_registry as orquestrador,
    initialize_registry,
    ModuleInfo,
)

# Inicializar o orquestrador se este módulo for importado diretamente
initialize_registry()

# Definir o que este módulo exporta
__all__ = [
    # Sistema de orquestração
    "orquestrador",
    "initialize_registry",
    "ModuleInfo",
    # Sistema de logging
    "add_log",
    "log_success",
    "log_error",
    "log_warning",
    "log_debug",
    "get_logs",
    "clear_logs",
    # Serviços
    "ImageAnalysisService",
    "HistoryService",
    "FirestoreService",
    "firestore_service",
    # Componentes de UI
    "show_history_sidebar",
    "show_service_selector",
    "show_plans_history_sidebar",
    "save_plan_to_history",
]
