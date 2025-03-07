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
import re
import pandas as pd
import logging

from firebase_service import FirebaseService
from ai_service import AIService
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
    Serviço para gerenciar tarefas no aplicativo.
    """
    
    def __init__(self, firebase_service=None):
        """
        Inicializa o serviço de tarefas.
        
        Args:
            firebase_service: Serviço Firebase para persistência
        """
        self.firebase = firebase_service or FirebaseService()
        self.ai = AIService(debug_mode=False)
        
        # Inicializar estado da sessão
        if 'tasks' not in st.session_state:
            st.session_state.tasks = []
        
        if 'task_added' not in st.session_state:
            st.session_state.task_added = False
    
    def load_tasks(self):
        """
        Carrega todas as tarefas do armazenamento.
        
        Returns:
            Lista de tarefas
        """
        # Se estiver usando Firebase, carregar de lá
        if not self.firebase.is_offline_mode:
            try:
                tasks = self.firebase.get_tasks()
                st.session_state.tasks = tasks
                return tasks
            except Exception as e:
                st.error(f"Erro ao carregar tarefas do Firebase: {str(e)}")
                logging.error(f"Erro ao carregar tarefas: {str(e)}")
                return []
        
        # Senão, usar armazenamento local
        return st.session_state.tasks
    
    def add_task(self, task_data):
        """
        Adiciona uma nova tarefa.
        
        Args:
            task_data: Dados da tarefa a ser adicionada
            
        Returns:
            ID da nova tarefa
        """
        task_id = str(uuid.uuid4())
        task_data['id'] = task_id
        task_data['created_at'] = datetime.now().isoformat()
        
        # Adicionar a tarefa localmente
        st.session_state.tasks.append(task_data)
        st.session_state.task_added = True
        
        # Salvar no Firebase se estiver conectado
        if not self.firebase.is_offline_mode:
            try:
                self.firebase.add_task(task_data)
            except Exception as e:
                st.error(f"Erro ao salvar tarefa no Firebase: {str(e)}")
                logging.error(f"Erro ao salvar tarefa: {str(e)}")
        
        return task_id
    
    def update_task(self, task_id, task_data):
        """
        Atualiza uma tarefa existente.
        
        Args:
            task_id: ID da tarefa a ser atualizada
            task_data: Novos dados da tarefa
            
        Returns:
            True se a atualização foi bem-sucedida
        """
        # Atualizar localmente
        for i, task in enumerate(st.session_state.tasks):
            if task.get('id') == task_id:
                st.session_state.tasks[i] = task_data
                
                # Salvar no Firebase se estiver conectado
                if not self.firebase.is_offline_mode:
                    try:
                        self.firebase.update_task(task_id, task_data)
                    except Exception as e:
                        st.error(f"Erro ao atualizar tarefa no Firebase: {str(e)}")
                        logging.error(f"Erro ao atualizar tarefa: {str(e)}")
                
                return True
        
        return False
    
    def delete_task(self, task_id):
        """
        Exclui uma tarefa.
        
        Args:
            task_id: ID da tarefa a ser excluída
            
        Returns:
            True se a exclusão foi bem-sucedida
        """
        # Excluir localmente
        for i, task in enumerate(st.session_state.tasks):
            if task.get('id') == task_id:
                del st.session_state.tasks[i]
                
                # Excluir do Firebase se estiver conectado
                if not self.firebase.is_offline_mode:
                    try:
                        self.firebase.delete_task(task_id)
                    except Exception as e:
                        st.error(f"Erro ao excluir tarefa do Firebase: {str(e)}")
                        logging.error(f"Erro ao excluir tarefa: {str(e)}")
                
                return True
        
        return False
    
    def generate_task_suggestions(self, description, image=None):
        """
        Gera sugestões de tarefas com base em uma descrição.
        
        Args:
            description: Descrição do projeto ou contexto
            image: Imagem opcional para processamento
            
        Returns:
            Lista de sugestões de tarefas
        """
        try:
            # Processar imagem se houver
            img_data = None
            if image is not None:
                buffered = io.BytesIO()
                image.save(buffered, format="JPEG")
                img_data = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            # Construir prompt para o modelo
            prompt = f"""
            Você é um assistente especializado em organizar tarefas.
            Com base na seguinte descrição, sugira uma lista estruturada de tarefas:
            
            {description}
            
            Retorne APENAS o JSON a seguir, sem qualquer explicação adicional:
            
            ```json
            [
              {{
                "title": "Título da Tarefa 1",
                "description": "Descrição detalhada",
                "priority": "alta|média|baixa",
                "subtasks": [
                  {{"title": "Subtarefa 1.1", "description": "Descrição da subtarefa"}}
                ]
              }}
            ]
            ```
            """
            
            # Fazer a chamada para o modelo
            with st.spinner("Gerando sugestões de tarefas..."):
                if img_data:
                    response = self.ai.generate_text(prompt, max_tokens=1024, image=img_data)
                else:
                    response = self.ai.generate_text(prompt, max_tokens=1024)
            
            # Tratar a resposta
            if not response:
                st.error("Não foi possível gerar sugestões. Tente novamente.")
                return []
            
            # Extrair JSON
            json_match = re.search(r'```json(.*?)```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1).strip()
            else:
                json_str = response.strip()
            
            # Remover caracteres invisíveis e parsear
            json_str = json_str.replace('\u200b', '')
            tasks = json.loads(json_str)
            
            return tasks
        except Exception as e:
            st.error(f"Erro ao gerar sugestões: {str(e)}")
            logging.error(f"Erro ao gerar sugestões de tarefas: {str(e)}")
            return []
    
    def export_tasks_to_csv(self):
        """
        Exporta as tarefas para um arquivo CSV.
        
        Returns:
            Bytes do arquivo CSV
        """
        tasks = self.load_tasks()
        if not tasks:
            return None
        
        # Preparar dados para o CSV
        rows = []
        for task in tasks:
            main_task = {
                'id': task.get('id', ''),
                'title': task.get('title', ''),
                'description': task.get('description', ''),
                'priority': task.get('priority', ''),
                'completed': task.get('completed', False),
                'parent_id': '',
                'created_at': task.get('created_at', '')
            }
            rows.append(main_task)
            
            # Adicionar subtarefas
            for subtask in task.get('subtasks', []):
                sub = {
                    'id': subtask.get('id', ''),
                    'title': subtask.get('title', ''),
                    'description': subtask.get('description', ''),
                    'priority': '',
                    'completed': subtask.get('completed', False),
                    'parent_id': task.get('id', ''),
                    'created_at': ''
                }
                rows.append(sub)
        
        # Criar DataFrame e exportar
        df = pd.DataFrame(rows)
        return df.to_csv(index=False).encode('utf-8') 