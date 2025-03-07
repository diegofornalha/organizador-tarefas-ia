import os
import json
import uuid
import base64
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, TypedDict, Sequence
import streamlit as st
from PIL import Image
import io
import requests
import asyncio

from firebase_service import FirebaseService
from gemini_service import GeminiService
from config import gemini_api_key

# Tipos de dados para tarefas
class Task(TypedDict, total=False):
    id: str
    title: str
    priority: Optional[str]  # 'Baixa', 'Média', 'Alta'
    completed: bool
    owner: str
    created_time: datetime
    due_date: datetime
    order: Optional[int]
    parent_id: Optional[str]  # Apenas para subtarefas
    completed_at: Optional[datetime]

class GeneratedTasks(TypedDict):
    title: str
    subtasks: List[str]

class TaskService:
    """
    Serviço para gerenciar tarefas com integração ao Firebase e Gemini API.
    """
    _instance = None
    
    def __new__(cls):
        """
        Implementação de Singleton para garantir apenas uma instância do serviço.
        """
        if cls._instance is None:
            cls._instance = super(TaskService, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance
    
    def __init__(self):
        """
        Inicializa o serviço de tarefas.
        """
        if not hasattr(self, 'initialized') or not self.initialized:
            try:
                self.firebase = FirebaseService()
            except Exception as e:
                st.error(f"Erro ao inicializar Firebase: {str(e)}")
                st.warning("Usando armazenamento local para tarefas.")
            
            try:
                self.gemini = GeminiService()
            except Exception as e:
                st.error(f"Erro ao inicializar Gemini: {str(e)}")
            
            # Gerar ID local para usuários não autenticados
            if "user_id" not in st.session_state:
                st.session_state.user_id = f"local-{str(uuid.uuid4())}"
                
            self.current_user_id = st.session_state.user_id
            self.collection_name = "todos"
            self.initialized = True
    
    def get_all_tasks(self) -> Sequence[Dict[str, Any]]:
        """
        Recupera todas as tarefas principais (não subtarefas).
        
        Returns:
            Lista de tarefas
        """
        try:
            tasks = self.firebase.get_documents(self.collection_name)
            # Filtrar apenas tarefas principais (sem parent_id)
            main_tasks = [task for task in tasks if "parent_id" not in task]
            return main_tasks
        except Exception as e:
            st.error(f"Erro ao carregar tarefas: {str(e)}")
            return []
    
    def get_subtasks(self, parent_id: str) -> Sequence[Dict[str, Any]]:
        """
        Recupera todas as subtarefas de uma tarefa principal.
        
        Args:
            parent_id: ID da tarefa principal
            
        Returns:
            Lista de subtarefas
        """
        try:
            all_tasks = self.firebase.get_documents(self.collection_name)
            # Filtrar apenas subtarefas com o parent_id especificado
            subtasks = [task for task in all_tasks if task.get("parent_id") == parent_id]
            # Ordenar por ordem se disponível
            subtasks.sort(key=lambda x: x.get("order", 0))
            return subtasks
        except Exception as e:
            st.error(f"Erro ao carregar subtarefas: {str(e)}")
            return []
    
    def add_task(self, title: str, due_date: datetime, priority: str = "Média") -> Optional[str]:
        """
        Adiciona uma nova tarefa.
        
        Args:
            title: Título da tarefa
            due_date: Data de vencimento
            priority: Prioridade da tarefa
            
        Returns:
            ID da tarefa criada ou None em caso de erro
        """
        try:
            task_data = {
                "title": title,
                "completed": False,
                "priority": priority,
                "created_time": datetime.now(),
                "due_date": due_date,
                "owner": self.current_user_id
            }
            
            task_id = self.firebase.add_document(self.collection_name, task_data)
            return task_id
        except Exception as e:
            st.error(f"Erro ao adicionar tarefa: {str(e)}")
            return None
    
    def add_task_with_subtasks(self, title: str, subtask_titles: List[str], 
                              due_date: datetime, priority: str = "Média") -> bool:
        """
        Adiciona uma tarefa principal com suas subtarefas.
        
        Args:
            title: Título da tarefa principal
            subtask_titles: Lista de títulos das subtarefas
            due_date: Data de vencimento
            priority: Prioridade da tarefa
            
        Returns:
            True se a operação for bem-sucedida, False caso contrário
        """
        try:
            # Adicionar tarefa principal
            main_task_id = self.add_task(title, due_date, priority)
            
            if not main_task_id:
                return False
            
            # Adicionar subtarefas
            for i, subtask_title in enumerate(subtask_titles):
                subtask_data = {
                    "title": subtask_title,
                    "completed": False,
                    "parent_id": main_task_id,
                    "order": i,
                    "created_time": datetime.now(),
                    "owner": self.current_user_id
                }
                
                self.firebase.add_document(self.collection_name, subtask_data)
            
            return True
        except Exception as e:
            st.error(f"Erro ao adicionar tarefa com subtarefas: {str(e)}")
            return False
    
    def complete_task(self, task_id: str) -> bool:
        """
        Marca uma tarefa como concluída.
        
        Args:
            task_id: ID da tarefa
            
        Returns:
            True se a operação for bem-sucedida, False caso contrário
        """
        try:
            # Verificar se é uma tarefa principal
            task = None
            tasks = self.firebase.get_documents(self.collection_name)
            for t in tasks:
                if t.get("id") == task_id:
                    task = t
                    break
            
            if not task:
                return False
            
            # Marcar como concluída com timestamp
            update_data = {
                "completed": True,
                "completed_at": datetime.now()
            }
            
            result = self.firebase.update_document(self.collection_name, task_id, update_data)
            
            # Se for uma tarefa principal, marcar subtarefas também
            if "parent_id" not in task:
                subtasks = self.get_subtasks(task_id)
                for subtask in subtasks:
                    self.firebase.update_document(self.collection_name, subtask.get("id", ""), update_data)
            
            return result
        except Exception as e:
            st.error(f"Erro ao concluir tarefa: {str(e)}")
            return False
    
    def delete_task_with_subtasks(self, task_id: str) -> bool:
        """
        Exclui uma tarefa e suas subtarefas.
        
        Args:
            task_id: ID da tarefa
            
        Returns:
            True se a operação for bem-sucedida, False caso contrário
        """
        try:
            # Excluir subtarefas primeiro
            subtasks = self.get_subtasks(task_id)
            for subtask in subtasks:
                self.firebase.delete_document(self.collection_name, subtask.get("id", ""))
            
            # Excluir tarefa principal
            return self.firebase.delete_document(self.collection_name, task_id)
        except Exception as e:
            st.error(f"Erro ao excluir tarefa: {str(e)}")
            return False
    
    def update_task(self, task_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Atualiza os dados de uma tarefa.
        
        Args:
            task_id: ID da tarefa
            update_data: Dados a serem atualizados
            
        Returns:
            True se a operação for bem-sucedida, False caso contrário
        """
        try:
            return self.firebase.update_document(self.collection_name, task_id, update_data)
        except Exception as e:
            st.error(f"Erro ao atualizar tarefa: {str(e)}")
            return False
    
    async def generate_tasks_from_prompt(self, prompt: str, 
                                        image: Optional[Image.Image] = None) -> Optional[GeneratedTasks]:
        """
        Gera tarefas usando a API Gemini a partir de um prompt e opcionalmente uma imagem.
        
        Args:
            prompt: Texto de prompt para gerar tarefas
            image: Imagem opcional para processamento multimodal
            
        Returns:
            Objeto com tarefas geradas ou None em caso de erro
        """
        try:
            # Verificar se o serviço Gemini está disponível
            if not hasattr(self, 'gemini') or not self.gemini:
                st.error("Serviço Gemini não disponível")
                return {
                    "title": "Tarefa baseada em: " + prompt[:30] + "...",
                    "subtasks": ["Subtarefa 1", "Subtarefa 2", "Subtarefa 3"]
                }
            
            # Criar prompt com instrução de formatação JSON
            formatted_prompt = f"""
            Ajude-me a planejar uma tarefa com subtarefas baseada no seguinte contexto: {prompt}
            
            IMPORTANTE: Responda APENAS com um objeto JSON no seguinte formato sem nenhum texto adicional:
            {{
                "title": "Título da tarefa principal (máximo 7 palavras)",
                "subtasks": [
                    "Subtarefa 1",
                    "Subtarefa 2",
                    "Subtarefa 3",
                    ...
                ]
            }}
            
            Não inclua explicações, apenas o JSON limpo.
            """
            
            # Converter imagem para uma parte do prompt se fornecida
            img_str = None
            if image:
                try:
                    buffered = io.BytesIO()
                    image.save(buffered, format="JPEG")
                    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
                except Exception as e:
                    st.warning(f"Erro ao processar imagem: {str(e)}")
            
            # Gerar resposta da API
            if img_str:
                response = self.gemini.generate_text(
                    formatted_prompt, 
                    image=img_str
                )
            else:
                response = self.gemini.generate_text(formatted_prompt)
            
            # Analisar resposta JSON
            try:
                # Limpar a resposta de possíveis texto extra
                response_text = response.strip()
                
                # Se a resposta contém blocos de código, extrair apenas o conteúdo JSON
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1]
                    response_text = response_text.split("```")[0].strip()
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].strip()
                
                # Converter para objeto Python
                result = json.loads(response_text)
                
                # Limitar a 10 subtarefas
                if "subtasks" in result and len(result.get("subtasks", [])) > 10:
                    result["subtasks"] = result.get("subtasks", [])[:10]
                
                # Validar estrutura
                if "title" not in result or "subtasks" not in result:
                    raise ValueError("Resposta não contém os campos esperados")
                
                return result
            except Exception as e:
                st.error(f"Erro ao processar resposta do Gemini: {str(e)}")
                # Fallback para formato padrão em caso de erro
                return {
                    "title": f"Plano para: {prompt[:30]}...",
                    "subtasks": [
                        "Etapa 1: Definir objetivos",
                        "Etapa 2: Pesquisar opções",
                        "Etapa 3: Implementar solução"
                    ]
                }
                
        except Exception as e:
            st.error(f"Erro ao gerar tarefas: {str(e)}")
            return None 