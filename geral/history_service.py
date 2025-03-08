"""
Serviço de histórico usando Firestore.
Este módulo gerencia o histórico de ações do usuário no aplicativo.
"""
from datetime import datetime
from typing import Dict, Any, Optional, List

# Importar logger - usando importação absoluta em vez de relativa
try:
    # Primeiro tenta importar como parte de um pacote (quando usado na aplicação principal)
    from .app_logger import log_success, log_error, log_warning
except ImportError:
    # Caso falhe, tenta importar diretamente (quando executado como script)
    from app_logger import log_success, log_error, log_warning


class HistoryService:
    """
    Serviço para gerenciar o histórico de ações do usuário com Firestore.
    """

    def __init__(self, firebase_service=None):
        """
        Inicializa o serviço de histórico.

        Args:
            firebase_service: Serviço Firebase para persistência (opcional)
        """
        # Importar FirebaseService aqui para evitar dependência circular
        if firebase_service is None:
            try:
                from firebase_service import FirebaseService
                firebase_service = FirebaseService()
            except Exception:
                log_warning(
                    "Firebase Service não disponível, usando armazenamento local"
                )
                firebase_service = None

        self.firebase = firebase_service
        self.collection_name = "historico"

        # Verificar se temos um serviço Firebase
        if self.firebase:
            # Verificar e criar a coleção se não existir
            self._ensure_collection_exists()

    def _ensure_collection_exists(self):
        """Verifica se a coleção de histórico existe e a cria se necessário."""
        try:
            # Verificar se temos Firebase, tem o atributo is_offline_mode, e não está offline
            has_firebase = self.firebase and hasattr(self.firebase, 'is_offline_mode')
            if has_firebase and not self.firebase.is_offline_mode:
                # Apenas verificar se a coleção existe
                self.firebase.get_collection(self.collection_name)
        except Exception as e:
            log_error(f"Erro ao verificar coleção de histórico: {str(e)}")

    def add_history_entry(
        self, action_type: str, description: str, data: Optional[Dict] = None
    ) -> bool:
        """
        Adiciona uma entrada ao histórico.

        Args:
            action_type: Tipo de ação (ex: "plan_generation", "task_creation")
            description: Descrição da ação
            data: Dados adicionais relacionados à ação (opcional)

        Returns:
            bool: True se adicionado com sucesso
        """
        try:
            # Se não temos Firebase, apenas simular sucesso
            if not self.firebase:
                log_success(f"Simulando adição ao histórico: {description}")
                return True

            # Criar objeto de histórico
            entry = {
                "action_type": action_type,
                "description": description,
                "timestamp": datetime.now().isoformat(),
                "data": data or {}
            }

            # Salvar no Firestore
            entry_id = self.firebase.add_document(self.collection_name, entry)

            if entry_id:
                log_success(f"Entrada de histórico adicionada: {description}")
                return True
            return False

        except Exception as e:
            log_error(f"Erro ao adicionar entrada ao histórico: {str(e)}")
            return False

    def get_history(
        self, limit: int = 10, action_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Recupera entradas do histórico.

        Args:
            limit: Número máximo de entradas para retornar
            action_type: Filtrar por tipo de ação (opcional)

        Returns:
            List: Lista de entradas do histórico
        """
        try:
            # Se não temos Firebase, retornar lista vazia
            if not self.firebase:
                return []

            # Obter todas as entradas
            entries = self.firebase.get_documents(self.collection_name)

            # Ordenar por timestamp (mais recentes primeiro)
            entries.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

            # Filtrar por tipo se especificado
            if action_type:
                entries = [
                    e for e in entries
                    if e.get('action_type') == action_type
                ]

            # Limitar número de resultados
            return entries[:limit]

        except Exception as e:
            log_error(f"Erro ao recuperar histórico: {str(e)}")
            return []

    def clear_history(self) -> bool:
        """
        Limpa todo o histórico.

        Returns:
            bool: True se o histórico foi limpo com sucesso
        """
        try:
            # Se não temos Firebase, apenas simular sucesso
            if not self.firebase:
                log_success("Simulação: Histórico limpo com sucesso")
                return True

            # Obter todas as entradas
            entries = self.firebase.get_documents(self.collection_name)

            # Excluir cada entrada
            for entry in entries:
                self.firebase.delete_document(
                    self.collection_name, entry['id']
                )

            log_success("Histórico limpo com sucesso")
            return True

        except Exception as e:
            log_error(f"Erro ao limpar histórico: {str(e)}")
            return False

    def register_plan_generation(
        self, prompt: str, has_image: bool = False
    ) -> bool:
        """
        Registra uma geração de plano no histórico.

        Args:
            prompt: Descrição usada para gerar o plano
            has_image: Se incluiu uma imagem

        Returns:
            bool: True se registrado com sucesso
        """
        # Truncar descrição longa
        text = prompt[:50] + "..." if len(prompt) > 50 else prompt
        desc = f"Plano gerado: {text}"

        data = {
            "prompt": prompt,
            "has_image": has_image
        }
        return self.add_history_entry("plan_generation", desc, data)

    def register_task_creation(
        self, task_title: str, source: str = "manual"
    ) -> bool:
        """
        Registra a criação de uma tarefa no histórico.

        Args:
            task_title: Título da tarefa criada
            source: Fonte da criação (manual, plano, etc)

        Returns:
            bool: True se registrado com sucesso
        """
        description = f"Tarefa criada: {task_title}"
        data = {
            "title": task_title,
            "source": source
        }
        return self.add_history_entry("task_creation", description, data)
