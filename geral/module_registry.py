"""
Sistema de registro e gerenciamento de módulos para o orquestrador.

Este módulo implementa um sistema de registro que permite:
1. Registrar módulos disponíveis
2. Carregar módulos dinamicamente
3. Gerenciar dependências entre módulos
4. Fornecer interfaces unificadas para acessar funcionalidades
"""

import os
import sys
import importlib
from typing import Dict, List, Any, Callable, Optional, Tuple, Set
import inspect
from dataclasses import dataclass

# Importar sistema de logging
try:
    from .app_logger import log_success, log_error, log_warning
except ImportError:
    # Funções padrão para uso quando as importações falham
    def log_success(message):
        print(f"SUCCESS: {message}")

    def log_error(message):
        print(f"ERROR: {message}")

    def log_warning(message):
        print(f"WARNING: {message}")


@dataclass
class ModuleInfo:
    """Armazena informações sobre um módulo registrado."""

    name: str
    path: str
    description: str = ""
    version: str = "0.1.0"
    dependencies: List[str] = None
    is_loaded: bool = False
    module_instance: Any = None
    exported_components: Dict[str, Any] = None
    interfaces: Dict[str, Any] = None
    service_url: str = ""
    port: int = 0

    def __post_init__(self):
        """Inicialização após a criação do objeto."""
        if self.dependencies is None:
            self.dependencies = []
        if self.exported_components is None:
            self.exported_components = {}
        if self.interfaces is None:
            self.interfaces = {}


class ModuleRegistry:
    """
    Registro centralizado de módulos disponíveis no sistema.
    Gerencia o carregamento, as dependências e as interfaces entre módulos.
    """

    def __init__(self):
        """Inicializa o registro de módulos."""
        self.modules: Dict[str, ModuleInfo] = {}
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.module_paths: Dict[str, str] = {
            "geral": os.path.join(self.base_path, "geral"),
            "servicos_modularizados": os.path.join(
                self.base_path, "servicos_modularizados"
            ),
        }

    def register_module(self, module_info: ModuleInfo) -> bool:
        """
        Registra um novo módulo no sistema.

        Args:
            module_info: Informações sobre o módulo a ser registrado

        Returns:
            bool: True se o registro foi bem-sucedido, False caso contrário
        """
        if module_info.name in self.modules:
            log_warning(
                f"Módulo '{module_info.name}' já está registrado. Sobrescrevendo."
            )

        self.modules[module_info.name] = module_info
        log_success(f"Módulo '{module_info.name}' registrado com sucesso.")
        return True

    def discover_modules(self) -> List[str]:
        """
        Descobre automaticamente os módulos disponíveis na estrutura de diretórios.

        Returns:
            List[str]: Lista de nomes dos módulos descobertos
        """
        discovered_modules = []

        # Procurar na pasta servicos_modularizados
        services_path = self.module_paths.get("servicos_modularizados")
        if os.path.exists(services_path) and os.path.isdir(services_path):
            for item in os.listdir(services_path):
                item_path = os.path.join(services_path, item)
                # Verificar se é um diretório e tem __init__.py
                if os.path.isdir(item_path) and os.path.exists(
                    os.path.join(item_path, "__init__.py")
                ):
                    module_info = ModuleInfo(
                        name=item,
                        path=item_path,
                        description=f"Módulo '{item}' (descoberto automaticamente)",
                    )
                    self.register_module(module_info)
                    discovered_modules.append(item)

        log_success(
            f"Descobertos {len(discovered_modules)} módulos: {', '.join(discovered_modules)}"
        )
        return discovered_modules

    def load_module(self, module_name: str) -> bool:
        """
        Carrega um módulo pelo nome.

        Args:
            module_name: Nome do módulo a ser carregado

        Returns:
            bool: True se o carregamento foi bem-sucedido, False caso contrário
        """
        if module_name not in self.modules:
            log_error(f"Módulo '{module_name}' não está registrado.")
            return False

        module_info = self.modules[module_name]
        if module_info.is_loaded:
            log_success(f"Módulo '{module_name}' já está carregado.")
            return True

        # Adicionar o caminho ao sys.path se necessário
        if module_info.path not in sys.path:
            sys.path.insert(0, module_info.path)

        # Verificar dependências
        if module_info.dependencies:
            for dep in module_info.dependencies:
                if dep not in self.modules or not self.modules[dep].is_loaded:
                    success = self.load_module(dep)
                    if not success:
                        log_error(
                            f"Não foi possível carregar a dependência '{dep}' para '{module_name}'."
                        )
                        return False

        # Tentar importar o módulo
        try:
            # Para módulos em services_modularizados, usamos o path relativo
            if "servicos_modularizados" in module_info.path:
                parent_dir = os.path.basename(os.path.dirname(module_info.path))
                import_path = f"{parent_dir}.{module_name}"
            else:
                # Para outros módulos, usamos apenas o nome
                import_path = module_name

            module_instance = importlib.import_module(import_path)
            module_info.module_instance = module_instance

            # Extrair componentes exportados
            if hasattr(module_instance, "__all__"):
                for component_name in module_instance.__all__:
                    if hasattr(module_instance, component_name):
                        component = getattr(module_instance, component_name)
                        module_info.exported_components[component_name] = component

            module_info.is_loaded = True
            log_success(f"Módulo '{module_name}' carregado com sucesso.")
            return True

        except ImportError as e:
            log_error(f"Erro ao importar módulo '{module_name}': {str(e)}")
            return False
        except Exception as e:
            log_error(f"Erro ao carregar módulo '{module_name}': {str(e)}")
            return False

    def get_module(self, module_name: str) -> Optional[ModuleInfo]:
        """
        Obtém informações sobre um módulo registrado.

        Args:
            module_name: Nome do módulo

        Returns:
            Optional[ModuleInfo]: Informações do módulo ou None se não existir
        """
        return self.modules.get(module_name)

    def get_component(self, module_name: str, component_name: str) -> Any:
        """
        Obtém um componente específico de um módulo.

        Args:
            module_name: Nome do módulo
            component_name: Nome do componente

        Returns:
            Any: O componente solicitado ou None se não existir
        """
        module_info = self.get_module(module_name)
        if not module_info or not module_info.is_loaded:
            return None

        return module_info.exported_components.get(component_name)

    def list_available_modules(self) -> List[str]:
        """
        Lista os nomes de todos os módulos registrados.

        Returns:
            List[str]: Lista de nomes dos módulos
        """
        return list(self.modules.keys())

    def list_loaded_modules(self) -> List[str]:
        """
        Lista os nomes de todos os módulos carregados.

        Returns:
            List[str]: Lista de nomes dos módulos carregados
        """
        return [name for name, info in self.modules.items() if info.is_loaded]

    def get_module_interfaces(self, module_name: str) -> Dict[str, Any]:
        """
        Obtém as interfaces disponíveis para um módulo.

        Args:
            module_name: Nome do módulo

        Returns:
            Dict[str, Any]: Dicionário de interfaces do módulo
        """
        module_info = self.get_module(module_name)
        if not module_info or not module_info.is_loaded:
            return {}

        return module_info.interfaces


# Instância global do registro de módulos
module_registry = ModuleRegistry()


def initialize_registry() -> ModuleRegistry:
    """
    Inicializa o registro de módulos, descobrindo e registrando os módulos disponíveis.

    Returns:
        ModuleRegistry: A instância do registro de módulos
    """
    # Registrar o módulo geral
    geral_info = ModuleInfo(
        name="geral",
        path=os.path.dirname(os.path.abspath(__file__)),
        description="Módulo central com serviços compartilhados e componentes reutilizáveis",
        version="1.0.0",
    )
    module_registry.register_module(geral_info)

    # Descobrir outros módulos
    module_registry.discover_modules()

    # Carregar o módulo geral
    module_registry.load_module("geral")

    return module_registry
