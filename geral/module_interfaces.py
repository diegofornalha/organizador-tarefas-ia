"""
Interfaces para componentes e serviços entre módulos.

Este módulo define interfaces formais que os módulos devem implementar
para garantir a interoperabilidade e facilitar a orquestração.
"""

import abc
from typing import Dict, List, Any, Optional, Union
from datetime import datetime


class PlanningInterface(abc.ABC):
    """Interface para serviços de planejamento."""

    @abc.abstractmethod
    def generate_plan(self, context: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Gera um plano baseado no contexto fornecido.

        Args:
            context: O contexto para geração do plano (texto, descrição)
            options: Opções adicionais para controlar a geração

        Returns:
            Dict contendo o plano gerado
        """
        pass

    @abc.abstractmethod
    def save_plan(self, plan: Dict[str, Any]) -> bool:
        """
        Salva um plano no armazenamento.

        Args:
            plan: O plano a ser salvo

        Returns:
            bool: True se salvo com sucesso, False caso contrário
        """
        pass

    @abc.abstractmethod
    def get_plans(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Recupera planos do armazenamento.

        Args:
            filters: Filtros para recuperar planos específicos

        Returns:
            Lista de planos
        """
        pass


class TasksInterface(abc.ABC):
    """Interface para serviços de tarefas."""

    @abc.abstractmethod
    def create_task(self,
                   title: str,
                   description: str = "",
                   deadline: Optional[datetime] = None,
                   plan_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Cria uma nova tarefa.

        Args:
            title: Título da tarefa
            description: Descrição da tarefa
            deadline: Data limite para conclusão
            plan_id: ID do plano associado (se houver)

        Returns:
            Dict com os dados da tarefa criada
        """
        pass

    @abc.abstractmethod
    def update_task(self, task_id: str, data: Dict[str, Any]) -> bool:
        """
        Atualiza uma tarefa existente.

        Args:
            task_id: ID da tarefa
            data: Dados a serem atualizados

        Returns:
            bool: True se atualizado com sucesso, False caso contrário
        """
        pass

    @abc.abstractmethod
    def get_tasks(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Recupera tarefas do armazenamento.

        Args:
            filters: Filtros para recuperar tarefas específicas

        Returns:
            Lista de tarefas
        """
        pass

    @abc.abstractmethod
    def delete_task(self, task_id: str) -> bool:
        """
        Exclui uma tarefa.

        Args:
            task_id: ID da tarefa a ser excluída

        Returns:
            bool: True se excluído com sucesso, False caso contrário
        """
        pass


class ImageAnalysisInterface(abc.ABC):
    """Interface para serviços de análise de imagem."""

    @abc.abstractmethod
    def analyze_image(self, image_data: Any) -> Dict[str, Any]:
        """
        Analisa uma imagem e retorna informações sobre ela.

        Args:
            image_data: Dados da imagem a ser analisada

        Returns:
            Dict com resultados da análise
        """
        pass

    @abc.abstractmethod
    def generate_planning_from_image(self,
                                    image_data: Any,
                                    description: str = "") -> Dict[str, Any]:
        """
        Gera um plano baseado em uma imagem.

        Args:
            image_data: Dados da imagem
            description: Descrição adicional para contextualizar a imagem

        Returns:
            Dict com o plano gerado
        """
        pass


class HistoryInterface(abc.ABC):
    """Interface para serviços de histórico."""

    @abc.abstractmethod
    def add_entry(self,
                 entry_type: str,
                 data: Dict[str, Any],
                 timestamp: Optional[datetime] = None) -> str:
        """
        Adiciona uma entrada ao histórico.

        Args:
            entry_type: Tipo da entrada (plano, tarefa, etc.)
            data: Dados da entrada
            timestamp: Momento da entrada (usa o momento atual se não fornecido)

        Returns:
            ID da entrada criada
        """
        pass

    @abc.abstractmethod
    def get_entries(self,
                   entry_type: Optional[str] = None,
                   limit: int = 20) -> List[Dict[str, Any]]:
        """
        Recupera entradas do histórico.

        Args:
            entry_type: Filtrar por tipo de entrada
            limit: Número máximo de entradas a retornar

        Returns:
            Lista de entradas do histórico
        """
        pass

    @abc.abstractmethod
    def clear_history(self, entry_type: Optional[str] = None) -> bool:
        """
        Limpa o histórico.

        Args:
            entry_type: Limpar apenas entradas deste tipo (se especificado)

        Returns:
            bool: True se operação bem-sucedida, False caso contrário
        """
        pass


class UIComponentInterface(abc.ABC):
    """Interface para componentes de UI reutilizáveis."""

    @abc.abstractmethod
    def render(self, container: Any, config: Optional[Dict[str, Any]] = None) -> Any:
        """
        Renderiza o componente de UI em um container.

        Args:
            container: Container Streamlit onde renderizar o componente
            config: Configurações adicionais para o componente

        Returns:
            Resultado da renderização (se aplicável)
        """
        pass
