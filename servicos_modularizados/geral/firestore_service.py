"""
Serviço de integração com Firestore.
Este módulo fornece funcionalidades para persistência de dados no Firestore,
com foco em reutilização entre os diferentes módulos do sistema.
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Union

# Configurar caminho para importação do FirebaseService
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Importar logger
try:
    from .app_logger import log_success, log_error, log_warning
except ImportError:
    # Caso falhe, tenta importar diretamente (quando executado como script)
    from app_logger import log_success, log_error, log_warning

# Importar FirebaseService
try:
    from firebase_service import FirebaseService, FIREBASE_AVAILABLE
except ImportError:
    log_warning("Firebase não disponível, usando armazenamento local")
    FIREBASE_AVAILABLE = False
    FirebaseService = None


class FirestoreService:
    """
    Serviço para interagir com o Firestore, adaptado para os módulos do sistema.
    """

    _instance = None

    def __new__(cls):
        """
        Implementa padrão Singleton para garantir apenas uma instância do serviço.
        """
        if cls._instance is None:
            cls._instance = super(FirestoreService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """
        Inicializa o serviço Firestore.
        """
        # Verificar se já foi inicializado (para Singleton)
        if hasattr(self, "firebase"):
            return

        if FIREBASE_AVAILABLE:
            try:
                self.firebase = FirebaseService()
                self.is_offline_mode = getattr(self.firebase, "is_offline_mode", True)
                log_success("FirestoreService inicializado com sucesso")
            except Exception as e:
                log_error(f"Erro ao inicializar FirestoreService: {str(e)}")
                self.firebase = None
                self.is_offline_mode = True
        else:
            self.firebase = None
            self.is_offline_mode = True
            log_warning("FirestoreService em modo offline")

    # Métodos para gerenciamento de planos no histórico

    def save_plan_to_history(self, plan_data: Dict[str, Any]) -> bool:
        """
        Salva um plano no histórico do Firestore.

        Args:
            plan_data: Dados do plano (deve conter título e JSON)

        Returns:
            bool: True se salvo com sucesso, False caso contrário
        """
        if not self.firebase:
            log_warning("Firestore não disponível, plano não persistido")
            return False

        try:
            # Preparar dados para persistência
            doc_data = {
                "titulo": plan_data.get("titulo", "Plano sem título"),
                "json": plan_data.get("json", "{}"),
                "created_at": datetime.now().isoformat(),
                "tipo": "plano",
            }

            # Salvar no Firestore
            doc_id = self.firebase.add_document("planos_historico", doc_data)

            if doc_id:
                log_success(
                    f"Plano '{doc_data['titulo']}' salvo no histórico (ID: {doc_id})"
                )
                return True
            else:
                log_error("Erro ao salvar plano no histórico (ID não retornado)")
                return False

        except Exception as e:
            log_error(f"Erro ao salvar plano no histórico: {str(e)}")
            return False

    def get_plans_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Recupera o histórico de planos do Firestore.

        Args:
            limit: Número máximo de planos a retornar (padrão: 20)

        Returns:
            List[Dict]: Lista de planos do histórico
        """
        if not self.firebase:
            log_warning("Firestore não disponível, retornando lista vazia")
            return []

        try:
            # Recuperar documentos da coleção de planos
            documents = self.firebase.get_documents("planos_historico")

            # Ordenar por data de criação (mais recente primeiro)
            if documents:
                documents.sort(key=lambda x: x.get("created_at", ""), reverse=True)

            # Limitar quantidade
            return documents[:limit] if documents else []

        except Exception as e:
            log_error(f"Erro ao recuperar histórico de planos: {str(e)}")
            return []

    def clear_plans_history(self) -> bool:
        """
        Limpa todo o histórico de planos no Firestore.

        Returns:
            bool: True se limpo com sucesso, False caso contrário
        """
        if not self.firebase:
            log_warning("Firestore não disponível, histórico não foi limpo")
            return False

        try:
            # Obter todos os planos
            documents = self.firebase.get_documents("planos_historico")

            # Excluir cada documento
            success = True
            for doc in documents:
                if not self.firebase.delete_document("planos_historico", doc.get("id")):
                    success = False

            if success:
                log_success("Histórico de planos limpo com sucesso")
            else:
                log_warning("Alguns planos não puderam ser excluídos do histórico")

            return success

        except Exception as e:
            log_error(f"Erro ao limpar histórico de planos: {str(e)}")
            return False

    # Métodos auxiliares para compatibilidade com os novos módulos

    def get_collection(self, collection: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Obtém todos os documentos de uma coleção.

        Args:
            collection: Nome da coleção
            limit: Número máximo de documentos a retornar

        Returns:
            list: Lista de documentos
        """
        if not self.firebase:
            log_warning(f"Firestore não disponível ao obter coleção {collection}")
            return []

        try:
            # Obter documentos da coleção
            documents = self.firebase.get_documents(collection, limit)

            return documents if documents else []
        except Exception as e:
            log_error(f"Erro ao obter coleção {collection}: {str(e)}")
            return []

    def add_document(self, collection: str, data: Dict[str, Any]) -> Optional[str]:
        """
        Adiciona um documento a uma coleção.

        Args:
            collection: Nome da coleção
            data: Dados a serem adicionados

        Returns:
            str: ID do documento criado ou None em caso de erro
        """
        if not self.firebase:
            log_warning(
                f"Firestore não disponível ao adicionar documento em {collection}"
            )
            return None

        try:
            # Adicionar documento
            doc_id = self.firebase.add_document(collection, data)

            if doc_id:
                log_success(f"Documento adicionado em {collection} (ID: {doc_id})")
                return doc_id
            else:
                log_error(
                    f"Erro ao adicionar documento em {collection} (ID não retornado)"
                )
                return None
        except Exception as e:
            log_error(f"Erro ao adicionar documento em {collection}: {str(e)}")
            return None

    def delete_document(self, collection: str, doc_id: str) -> bool:
        """
        Exclui um documento de uma coleção.

        Args:
            collection: Nome da coleção
            doc_id: ID do documento

        Returns:
            bool: True se a operação foi bem-sucedida
        """
        if not self.firebase:
            log_warning(
                f"Firestore não disponível ao excluir documento {doc_id} de {collection}"
            )
            return False

        try:
            # Excluir documento
            success = self.firebase.delete_document(collection, doc_id)

            if success:
                log_success(f"Documento {doc_id} excluído de {collection}")
                return True
            else:
                log_error(f"Erro ao excluir documento {doc_id} de {collection}")
                return False
        except Exception as e:
            log_error(f"Erro ao excluir documento {doc_id} de {collection}: {str(e)}")
            return False


# Instância para uso direto
firestore_service = FirestoreService()
