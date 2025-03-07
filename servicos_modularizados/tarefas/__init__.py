"""
Módulo de gerenciamento de tarefas.
Este pacote contém ferramentas para organizar e acompanhar tarefas.
"""

# Exportar os componentes principais
try:
    from .components import (
        tasks_ui,
        tasks_standalone,
        criar_tarefas_do_plano,
        exibir_tarefa,
    )

    # Definir o que é exportado
    __all__ = [
        "tasks_ui",
        "tasks_standalone",
        "criar_tarefas_do_plano",
        "exibir_tarefa",
    ]
except ImportError:
    # Se não conseguir importar, é porque está sendo usado isoladamente
    pass
