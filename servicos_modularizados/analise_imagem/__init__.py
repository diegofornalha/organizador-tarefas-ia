"""
Módulo de análise de imagem com IA.
Este pacote contém ferramentas para análise de imagens e geração de planejamento.
"""

# Exportar os componentes principais
try:
    from .components import image_analysis_ui, image_analysis_standalone

    # Definir o que é exportado
    __all__ = ["image_analysis_ui", "image_analysis_standalone"]
except ImportError:
    # Se não conseguir importar, é porque está sendo usado isoladamente
    pass
