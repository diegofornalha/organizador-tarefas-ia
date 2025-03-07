import json
import os
from typing import Dict, Any, List, Optional, Union
import uuid
import streamlit as st

# Tentar importar o Firebase apenas se estiver disponível
try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    FIREBASE_AVAILABLE = True  # Permitir modo online
except ImportError:
    FIREBASE_AVAILABLE = False

try:
    from dotenv import load_dotenv
    # Carregar variáveis de ambiente
    load_dotenv()
except ImportError:
    pass

from config import firebase_config

class LocalStorageService:
    """
    Serviço de armazenamento local para quando o Firebase não estiver disponível.
    Implementa a mesma interface do FirebaseService.
    """
    def __init__(self):
        """
        Inicializa o armazenamento local usando o session_state do Streamlit.
        """
        if "local_storage" not in st.session_state:
            st.session_state.local_storage = {}
        self.storage = st.session_state.local_storage
    
    def get_collection(self, collection_name: str):
        """
        Obtém uma referência para uma coleção no armazenamento local.
        """
        if collection_name not in self.storage:
            self.storage[collection_name] = {}
        return collection_name
    
    def get_documents(self, collection_name: str) -> List[Dict[str, Any]]:
        """
        Recupera todos os documentos de uma coleção.
        """
        collection = self.get_collection(collection_name)
        if not collection or collection_name not in self.storage:
            return []
        
        documents = []
        for doc_id, data in self.storage[collection_name].items():
            doc_data = data.copy()
            doc_data['id'] = doc_id
            documents.append(doc_data)
        
        return documents
    
    def add_document(self, collection_name: str, data: Dict[str, Any]) -> Optional[str]:
        """
        Adiciona um documento a uma coleção.
        """
        collection = self.get_collection(collection_name)
        if not collection:
            return None
        
        doc_id = str(uuid.uuid4())
        self.storage[collection_name][doc_id] = data.copy()
        return doc_id
    
    def update_document(self, collection_name: str, document_id: str, data: Dict[str, Any]) -> bool:
        """
        Atualiza um documento existente.
        """
        collection = self.get_collection(collection_name)
        if not collection or document_id not in self.storage[collection_name]:
            return False
        
        # Atualizar dados existentes (não substituir completamente)
        for key, value in data.items():
            self.storage[collection_name][document_id][key] = value
        
        return True
    
    def delete_document(self, collection_name: str, document_id: str) -> bool:
        """
        Exclui um documento.
        """
        collection = self.get_collection(collection_name)
        if not collection or collection_name not in self.storage:
            return False
        
        # Verificar se o documento existe antes de excluir
        if document_id not in self.storage[collection_name]:
            print(f"Documento {document_id} não encontrado na coleção {collection_name}")
            return False
        
        # Excluir apenas o documento específico
        del self.storage[collection_name][document_id]
        print(f"Documento {document_id} excluído com sucesso")
        return True

class FirebaseService:
    """
    Serviço para interagir com o Firebase Firestore.
    """
    _instance = None
    
    def __new__(cls):
        """
        Implementação de Singleton para garantir apenas uma instância do serviço.
        """
        if cls._instance is None:
            cls._instance = super(FirebaseService, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance
    
    def __init__(self):
        """
        Inicializa o serviço Firebase.
        """
        if not self.initialized:
            self.config = firebase_config
            self.app = None
            self.db = None
            self.is_offline_mode = not FIREBASE_AVAILABLE
            
            # Tentar inicializar o Firebase Firestore se disponível
            if FIREBASE_AVAILABLE:
                try:
                    # Verificar se já existe uma instância do app
                    try:
                        self.app = firebase_admin.get_app()
                    except ValueError:
                        # Se não existir, criar nova instância
                        # Verificar se existe um arquivo de credenciais
                        cred_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
                        
                        if cred_path and os.path.exists(cred_path):
                            # Usar credenciais do arquivo
                            cred = credentials.Certificate(cred_path)
                            self.app = firebase_admin.initialize_app(cred)
                            print(f"Firebase inicializado com credenciais do arquivo: {cred_path}")
                        else:
                            # Se não houver arquivo, usar configuração padrão
                            self.app = firebase_admin.initialize_app()
                            print("Firebase inicializado com configuração padrão")
                    
                    # Conectar ao Firestore
                    self.db = firestore.client()
                    self.is_offline_mode = False
                    print("Firebase conectado com sucesso (modo online)")
                except Exception as e:
                    print(f"Erro ao conectar ao Firebase: {str(e)}")
                    self.is_offline_mode = True
            
            if self.is_offline_mode:
                self.local_storage = LocalStorageService()
                print("Usando modo offline (armazenamento local)")
            
            self.initialized = True
    
    def get_collection(self, collection_name: str):
        """
        Obtém uma referência para uma coleção.
        """
        if not self.is_offline_mode and self.db is not None:
            return self.db.collection(collection_name)
        return self.local_storage.get_collection(collection_name)
    
    def get_documents(self, collection_name: str) -> List[Dict[str, Any]]:
        """
        Recupera todos os documentos de uma coleção.
        """
        if not self.is_offline_mode and self.db is not None:
            try:
                collection_ref = self.get_collection(collection_name)
                if isinstance(collection_ref, str):
                    return self.local_storage.get_documents(collection_name)
                
                docs = collection_ref.get()
                result = []
                for doc in docs:
                    doc_dict = doc.to_dict()
                    if isinstance(doc_dict, dict):
                        doc_dict['id'] = doc.id
                        result.append(doc_dict)
                return result
            except Exception as e:
                print(f"Erro ao buscar documentos: {str(e)}")
                return []
        return self.local_storage.get_documents(collection_name)
    
    def add_document(self, collection_name: str, data: Dict[str, Any]) -> Optional[str]:
        """
        Adiciona um documento a uma coleção.
        """
        if not self.is_offline_mode and self.db is not None:
            try:
                collection_ref = self.get_collection(collection_name)
                if isinstance(collection_ref, str):
                    return self.local_storage.add_document(collection_name, data)
                
                doc_ref = collection_ref.document()
                doc_ref.set(data)
                return doc_ref.id
            except Exception as e:
                print(f"Erro ao adicionar documento: {str(e)}")
                return None
        return self.local_storage.add_document(collection_name, data)
    
    def update_document(self, collection_name: str, document_id: str, data: Dict[str, Any]) -> bool:
        """
        Atualiza um documento existente.
        """
        if not self.is_offline_mode and self.db is not None:
            try:
                collection_ref = self.get_collection(collection_name)
                if isinstance(collection_ref, str):
                    return self.local_storage.update_document(collection_name, document_id, data)
                
                doc_ref = collection_ref.document(document_id)
                doc_ref.update(data)
                return True
            except Exception as e:
                print(f"Erro ao atualizar documento: {str(e)}")
                return False
        return self.local_storage.update_document(collection_name, document_id, data)
    
    def delete_document(self, collection_name: str, document_id: str) -> bool:
        """
        Exclui um documento.
        """
        if not self.is_offline_mode and self.db is not None:
            try:
                collection_ref = self.get_collection(collection_name)
                if isinstance(collection_ref, str):
                    return self.local_storage.delete_document(collection_name, document_id)
                
                doc_ref = collection_ref.document(document_id)
                doc_ref.delete()
                return True
            except Exception as e:
                print(f"Erro ao excluir documento: {str(e)}")
                return False
        return self.local_storage.delete_document(collection_name, document_id)

    # Métodos para compatibilidade com o novo TaskService
    def get_tasks(self) -> List[Dict[str, Any]]:
        """
        Recupera todas as tarefas armazenadas.
        
        Returns:
            Lista de tarefas
        """
        # Usar a coleção "todos" para compatibilidade com código existente
        return self.get_documents("todos")

    def add_task(self, task_data: Dict[str, Any]) -> Optional[str]:
        """
        Adiciona uma nova tarefa.
        
        Args:
            task_data: Dados da tarefa a ser adicionada
            
        Returns:
            ID da nova tarefa ou None em caso de erro
        """
        return self.add_document("todos", task_data)

    def update_task(self, task_id: str, task_data: Dict[str, Any]) -> bool:
        """
        Atualiza uma tarefa existente.
        
        Args:
            task_id: ID da tarefa a ser atualizada
            task_data: Novos dados da tarefa
            
        Returns:
            True se a atualização foi bem-sucedida
        """
        return self.update_document("todos", task_id, task_data)

    def delete_task(self, task_id: str) -> bool:
        """
        Exclui uma tarefa.
        
        Args:
            task_id: ID da tarefa a ser excluída
            
        Returns:
            True se a exclusão foi bem-sucedida
        """
        return self.delete_document("todos", task_id) 