"""
Módulo de serviço Firebase para plano_tarefas.
Implementa a integração com o serviço Firebase principal do projeto.
"""

import os
import sys
from typing import List, Dict, Any, Optional

# Configurações de caminhos e imports
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICES_DIR = os.path.dirname(CURRENT_DIR)
ROOT_DIR = os.path.dirname(SERVICES_DIR)

# Caminho para o arquivo de credenciais
CREDENTIALS_PATH = os.path.join(
    ROOT_DIR, "firebase-config", "firebase-credentials.json"
)

# Adicionar diretórios ao path se necessário
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)


# Funções padrão para uso quando as importações falham
def log_success(message):
    print(f"SUCCESS: {message}")


def log_error(message):
    print(f"ERROR: {message}")


# Classe para armazenamento local
class TaskStorageService:
    """
    Serviço de armazenamento para tarefas.
    Implementa a integração com o Firebase ou armazenamento local.
    """

    def __init__(self):
        self.firebase_service = None
        self.is_offline_mode = True

        # Tentar importar o serviço Firebase principal
        try:
            # Importar o FirebaseService do projeto principal
            import firebase_service as root_firebase

            if hasattr(root_firebase, "FirebaseService"):
                self.firebase_service = root_firebase.FirebaseService()
                self.is_offline_mode = self.firebase_service.is_offline_mode
                log_success("Serviço Firebase principal conectado com sucesso")
            else:
                log_error("FirebaseService não encontrado no módulo principal")
                self._init_local_firebase()
        except Exception as e:
            erro_msg = f"Erro ao conectar com o serviço Firebase principal: {str(e)}"
            log_error(erro_msg)
            # Tentar inicializar Firebase localmente se o arquivo de credenciais existir
            self._init_local_firebase()

    def _init_local_firebase(self):
        """Inicializa o Firebase localmente se possível"""
        try:
            # Verificar se o arquivo de credenciais existe
            if os.path.exists(CREDENTIALS_PATH):
                log_success(f"Arquivo de credenciais encontrado: {CREDENTIALS_PATH}")
                try:
                    # Tentar inicializar Firebase localmente
                    import firebase_admin
                    from firebase_admin import credentials, firestore

                    # Inicializar Firebase
                    cred = credentials.Certificate(CREDENTIALS_PATH)
                    app = firebase_admin.initialize_app(cred)
                    db = firestore.client()

                    # Implementar interface compatível com FirebaseService
                    class LocalFirebaseService:
                        def __init__(self, db):
                            self.db = db
                            self.is_offline_mode = False

                        def get_tasks(self):
                            try:
                                collection = self.db.collection("todos")
                                docs = collection.get()
                                result = []
                                for doc in docs:
                                    doc_dict = doc.to_dict()
                                    doc_dict["id"] = doc.id
                                    result.append(doc_dict)
                                return result
                            except Exception as e:
                                log_error(f"Erro ao obter tarefas: {str(e)}")
                                return []

                        def add_task(self, task_data):
                            try:
                                # Remover o ID se existir para o Firestore gerar um novo
                                task_copy = task_data.copy()
                                if "id" in task_copy:
                                    task_id = task_copy.pop("id")

                                # Adicionar documento
                                doc_ref = self.db.collection("todos").document()
                                doc_ref.set(task_copy)
                                return doc_ref.id
                            except Exception as e:
                                log_error(f"Erro ao adicionar tarefa: {str(e)}")
                                return None

                        def update_task(self, task_id, task_data):
                            try:
                                # Remover o ID para não duplicar no documento
                                task_copy = task_data.copy()
                                if "id" in task_copy:
                                    del task_copy["id"]

                                # Atualizar documento
                                doc_ref = self.db.collection("todos").document(task_id)
                                doc_ref.update(task_copy)
                                return True
                            except Exception as e:
                                log_error(f"Erro ao atualizar tarefa: {str(e)}")
                                return False

                        def delete_task(self, task_id):
                            try:
                                doc_ref = self.db.collection("todos").document(task_id)
                                doc_ref.delete()
                                return True
                            except Exception as e:
                                log_error(f"Erro ao excluir tarefa: {str(e)}")
                                return False

                    # Usar a implementação local
                    self.firebase_service = LocalFirebaseService(db)
                    self.is_offline_mode = False
                    log_success("Firebase inicializado localmente com sucesso")
                except Exception as e:
                    log_error(f"Erro ao inicializar Firebase local: {str(e)}")
            else:
                log_error(f"Arquivo de credenciais não encontrado: {CREDENTIALS_PATH}")
        except Exception as e:
            log_error(f"Erro ao inicializar Firebase local: {str(e)}")

    def get_tasks(self) -> List[Dict[str, Any]]:
        """
        Recupera todas as tarefas armazenadas.

        Returns:
            Lista de tarefas
        """
        if not self.is_offline_mode and self.firebase_service is not None:
            try:
                return self.firebase_service.get_tasks()
            except Exception as e:
                log_error(f"Erro ao buscar tarefas do Firebase: {str(e)}")
                return []

        # Modo offline - retornar tarefas da sessão
        import streamlit as st

        if "tasks" not in st.session_state:
            st.session_state.tasks = []
        return st.session_state.tasks

    def add_task(self, task_data: Dict[str, Any]) -> Optional[str]:
        """
        Adiciona uma nova tarefa.

        Args:
            task_data: Dados da tarefa a ser adicionada

        Returns:
            ID da nova tarefa ou None em caso de erro
        """
        if not self.is_offline_mode and self.firebase_service is not None:
            try:
                return self.firebase_service.add_task(task_data)
            except Exception as e:
                log_error(f"Erro ao adicionar tarefa ao Firebase: {str(e)}")

        # Adicionar localmente
        import streamlit as st

        if "tasks" not in st.session_state:
            st.session_state.tasks = []

        # Se já tiver um ID, usar; senão, gerar um novo
        if "id" not in task_data or not task_data["id"]:
            import uuid

            task_data["id"] = str(uuid.uuid4())

        st.session_state.tasks.append(task_data)
        return task_data["id"]

    def update_task(self, task_id: str, task_data: Dict[str, Any]) -> bool:
        """
        Atualiza uma tarefa existente.

        Args:
            task_id: ID da tarefa a ser atualizada
            task_data: Novos dados da tarefa

        Returns:
            True se a atualização foi bem-sucedida
        """
        if not self.is_offline_mode and self.firebase_service is not None:
            try:
                return self.firebase_service.update_task(task_id, task_data)
            except Exception as e:
                log_error(f"Erro ao atualizar tarefa no Firebase: {str(e)}")

        # Atualizar localmente
        import streamlit as st

        if "tasks" not in st.session_state:
            st.session_state.tasks = []

        for i, task in enumerate(st.session_state.tasks):
            if task.get("id") == task_id:
                st.session_state.tasks[i] = task_data
                return True

        return False

    def delete_task(self, task_id: str) -> bool:
        """
        Exclui uma tarefa.

        Args:
            task_id: ID da tarefa a ser excluída

        Returns:
            True se a exclusão foi bem-sucedida
        """
        if not self.is_offline_mode and self.firebase_service is not None:
            try:
                return self.firebase_service.delete_task(task_id)
            except Exception as e:
                log_error(f"Erro ao excluir tarefa do Firebase: {str(e)}")

        # Excluir localmente
        import streamlit as st

        if "tasks" not in st.session_state:
            return False

        for i, task in enumerate(st.session_state.tasks):
            if task.get("id") == task_id:
                st.session_state.tasks.pop(i)
                return True

        return False
