import streamlit as st
from round_button import RoundButton
from datetime import datetime

class Task:
    """
    Componente de tarefa para Streamlit.
    """
    
    @staticmethod
    def render(task, key_prefix, can_delete=True, show_generated_with_gemini=False, 
               on_delete=None, on_tasks_completed_toggle=None):
        """
        Renderiza um componente de tarefa com suas subtarefas.
        
        Args:
            task: Dicionário com a tarefa principal e suas subtarefas
                 {'maintask': {...}, 'subtasks': [...]}
            key_prefix: Prefixo para as chaves dos componentes Streamlit
            can_delete: Se o botão de exclusão deve ser mostrado
            show_generated_with_gemini: Se deve mostrar o rótulo "Gerado pela API Gemini"
            on_delete: Callback quando o botão de exclusão é clicado
            on_tasks_completed_toggle: Callback quando uma tarefa/subtarefa é marcada
            
        Returns:
            None
        """
        # Verificar se a tarefa é válida
        if not task or 'maintask' not in task:
            st.warning("Tarefa inválida")
            return
        
        maintask = task['maintask']
        subtasks = task.get('subtasks', [])
        
        # Definir cores e estilos com base no status da tarefa
        is_completed = maintask.get('completed', False)
        status_color = "green" if is_completed else "gray"
        
        # Criar um título formatado com ícone de status
        check_icon = "✅" if is_completed else "⬜️"
        title = f"{check_icon} {maintask.get('title', 'Sem título')}"
        
        # Mostrar a contagem de subtarefas concluídas
        subtasks_completed = sum(1 for s in subtasks if s.get('completed', False))
        subtitle = f"{subtasks_completed}/{len(subtasks)} subtarefas concluídas" if subtasks else ""
        
        # Adicionar CSS para os estilos das tarefas
        st.markdown("""
        <style>
        .subtask-item {
            margin-left: 20px;
            padding: 5px;
            border-left: 1px solid rgba(255,255,255,0.1);
        }
        .task-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .task-title {
            margin-right: 10px;
        }
        .task-actions {
            display: flex;
            gap: 5px;
        }
        .completed-subtask {
            text-decoration: underline;
            opacity: 0.7;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Container para a tarefa
        with st.container():
            # Criar um expander para a tarefa principal (recolhido por padrão)
            expander = st.expander(title, expanded=False)
            
            # Área para as ações
            with expander:
                # Mostrar detalhes da tarefa
                col_actions = st.container()
                
                # Botões de ação para a tarefa principal
                with col_actions:
                    col1, col2, col3 = st.columns([1, 1, 8])
                    
                    # Botão para marcar como concluída/pendente
                    with col1:
                        toggle_status = st.button(
                            "✅" if not is_completed else "⬜️", 
                            key=f"{key_prefix}_toggle",
                            help="Marcar como completa/incompleta"
                        )
                        if toggle_status:
                            Task._handle_main_task_toggle(
                                maintask, subtasks, not is_completed, on_tasks_completed_toggle
                            )
                    
                    # Botão para excluir tarefa
                    if can_delete:
                        with col2:
                            if st.button("🗑️", key=f"{key_prefix}_delete", help="Excluir tarefa"):
                                if on_delete:
                                    # Passar o ID da tarefa principal
                                    on_delete(maintask.get("id", ""))
                
                # Mostrar subtarefas
                if subtasks:
                    st.markdown("### Subtarefas:")
                    
                    # Ordenar subtarefas (não concluídas primeiro, concluídas no final)
                    sorted_subtasks = sorted(subtasks, key=lambda x: x.get('completed', False))
                    
                    for i, subtask in enumerate(sorted_subtasks):
                        subtask_completed = subtask.get('completed', False)
                        subtask_icon = "✅" if subtask_completed else "⬜️"
                        
                        # Container para cada subtarefa
                        with st.container():
                            st.markdown(f"<div class='subtask-item'>", unsafe_allow_html=True)
                            
                            # Layout para a subtarefa
                            cols = st.columns([0.05, 0.8, 0.15])
                            
                            # Estado da subtarefa
                            with cols[0]:
                                if st.button(
                                    subtask_icon, 
                                    key=f"{key_prefix}_sub_{i}_toggle",
                                    help="Marcar subtarefa como completa/incompleta"
                                ):
                                    Task._handle_subtask_toggle(
                                        subtask, not subtask_completed, on_tasks_completed_toggle
                                    )
                            
                            # Título da subtarefa
                            with cols[1]:
                                # Adicionar classe para subtarefas concluídas (sublinhadas)
                                if subtask_completed:
                                    st.markdown(f"<div class='completed-subtask'>{subtask.get('title', 'Subtarefa')}</div>", unsafe_allow_html=True)
                                else:
                                    st.write(subtask.get('title', 'Subtarefa'))
                            
                            # Botão de exclusão para subtarefa
                            if can_delete:
                                with cols[2]:
                                    if st.button("🗑️", key=f"{key_prefix}_sub_{i}_delete", help="Excluir subtarefa"):
                                        if on_delete and "id" in subtask:
                                            # Importante: passamos diretamente o ID da subtarefa como string
                                            subtask_id = subtask.get("id", "")
                                            if subtask_id:
                                                on_delete(subtask_id)
                            
                            st.markdown("</div>", unsafe_allow_html=True)
                
                # Mostrar informações adicionais
                if show_generated_with_gemini:
                    st.markdown(
                        "<div style='text-align: right; font-size: 0.8em; color: #666;'>"
                        "Gerado pela API Gemini</div>",
                        unsafe_allow_html=True
                    )
    
    @staticmethod
    def _handle_main_task_toggle(maintask, subtasks, new_state, callback=None):
        """Atualiza o estado da tarefa principal e todas suas subtarefas."""
        maintask["completed"] = new_state
        
        # Atualizar todas as subtarefas também
        for subtask in subtasks:
            subtask["completed"] = new_state
        
        if callback:
            callback(maintask)
    
    @staticmethod
    def _handle_subtask_toggle(subtask, new_state, callback=None):
        """Atualiza o estado de uma subtarefa específica."""
        subtask["completed"] = new_state
        
        if callback:
            callback(subtask) 