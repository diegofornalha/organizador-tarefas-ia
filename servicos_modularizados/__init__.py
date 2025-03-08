"""
Pacote de serviços modularizados para o organizador de tarefas.
Este pacote contém:
- Módulo 'geral': serviços principais (logging, análise de imagem, histórico)
- Módulo 'analise_imagem': aplicação isolada para análise de imagens
"""

# Tentar importar as principais classes e funções
try:
    # Importar do módulo geral
    from .geral.app_logger import (
        add_log,
        log_success,
        log_error,
        log_warning,
        log_debug,
        get_logs,
        clear_logs,
    )
    from .geral.image_analysis_service import ImageAnalysisService
    from .geral.history_service import HistoryService
    from .geral.sidebar_components import show_history_sidebar, show_service_selector

    # Definir __all__ para indicar o que é exportado pelo pacote
    __all__ = [
        # Logger
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
        # Componentes UI
        "show_history_sidebar",
        "show_service_selector",
    ]
except ImportError:
    # Se não conseguir importar, é porque está sendo usado isoladamente
    pass
