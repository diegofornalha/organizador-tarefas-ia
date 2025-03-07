import streamlit as st

class RoundButton:
    """
    Componente de botão redondo para marcar tarefas como concluídas.
    """
    
    @staticmethod
    def render(title, key, checked=False, subtask=False, disabled=False, on_change=None):
        """
        Renderiza um botão redondo com título.
        
        Args:
            title: Texto do botão
            key: Chave única para o componente Streamlit
            checked: Se o botão está marcado
            subtask: Se é uma subtarefa (para estilo diferente)
            disabled: Se o botão está desativado
            on_change: Callback para mudança de estado
            
        Returns:
            bool: Estado atual do botão
        """
        # Estilo CSS para botão redondo
        st.markdown("""
        <style>
        .round-button {
            display: flex;
            align-items: center;
            margin-bottom: 5px;
        }
        .round-button input {
            margin-right: 10px;
        }
        .task-title {
            font-weight: bold;
            font-size: 16px;
            display: inline-block;
            margin-left: 10px;
        }
        .subtask-title {
            font-size: 14px;
            margin-left: 10px;
            display: inline-block;
        }
        .checkbox-container {
            display: flex;
            align-items: center;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Usar um único elemento para o checkbox em vez de colunas aninhadas
        new_state = st.checkbox(
            title, 
            value=checked, 
            key=f"btn_{key}", 
            disabled=disabled,
            label_visibility="visible"
        )
            
        # Chamar callback se o estado mudar
        if new_state != checked and on_change:
            on_change(new_state)
        
        return new_state 