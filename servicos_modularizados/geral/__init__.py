"""
Pacote de serviços modularizados para o organizador de tarefas.
Este módulo 'geral' contém serviços reutilizáveis para processamento
de imagens, logging, histórico e componentes de interface.
"""

# Exportar classes e funções principais
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
