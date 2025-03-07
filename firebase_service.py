import json
import os
from typing import Dict, Any, List, Optional
import uuid
import streamlit as st

# Tentar importar o Firebase apenas se estiver disponível
try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    FIREBASE_AVAILABLE = False  # Forçar modo offline para simplicidade
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
    No modo simplificado, sempre usa armazenamento local.
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
            self.is_offline_mode = True
            self.local_storage = LocalStorageService()
            print("Usando modo offline (armazenamento local)")
            self.initialized = True
    
    def get_collection(self, collection_name: str):
        """
        Obtém uma referência para uma coleção.
        """
        return self.local_storage.get_collection(collection_name)
    
    def get_documents(self, collection_name: str) -> List[Dict[str, Any]]:
        """
        Recupera todos os documentos de uma coleção.
        """
        return self.local_storage.get_documents(collection_name)
    
    def add_document(self, collection_name: str, data: Dict[str, Any]) -> Optional[str]:
        """
        Adiciona um documento a uma coleção.
        """
        return self.local_storage.add_document(collection_name, data)
    
    def update_document(self, collection_name: str, document_id: str, data: Dict[str, Any]) -> bool:
        """
        Atualiza um documento existente.
        """
        return self.local_storage.update_document(collection_name, document_id, data)
    
    def delete_document(self, collection_name: str, document_id: str) -> bool:
        """
        Exclui um documento.
        """
        return self.local_storage.delete_document(collection_name, document_id) 