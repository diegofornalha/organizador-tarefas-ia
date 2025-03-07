"""
Módulo de geração de planejamento com IA.
Este pacote contém ferramentas para criação de planos de tarefas.
"""

# Exportar os componentes principais
try:
    from .components import planning_ui, planning_standalone

    # Definir o que é exportado
    __all__ = ["planning_ui", "planning_standalone"]
except ImportError:
    # Se não conseguir importar, é porque está sendo usado isoladamente
    pass
