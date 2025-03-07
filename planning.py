import streamlit as st
import os
import base64
from PIL import Image
import asyncio
from datetime import datetime
import time
import io

from task_service import TaskService
from gemini_service import GeminiService

# Função para inicializar o estado da sessão
def init_session_state():
    if "plan_prompt" not in st.session_state:
        st.session_state.plan_prompt = ""
    if "plan_result" not in st.session_state:
        st.session_state.plan_result = None
    if "plan_loading" not in st.session_state:
        st.session_state.plan_loading = False
    if "image_uploaded" not in st.session_state:
        st.session_state.image_uploaded = None

# Gerar plano usando o Gemini
def generate_plan(prompt, image=None):
    st.session_state.plan_loading = True
    
    gemini_service = GeminiService()
    
    try:
        # Preparar o prompt
        formatted_prompt = f"""
        Crie um plano detalhado de tarefas e subtarefas baseado nesta solicitação: {prompt}
        
        ESTRUTURA DA RESPOSTA:
        1. [TÍTULO DO PLANO]
        
        Objetivo:
        - [DESCREVA BREVEMENTE O OBJETIVO]
        
        Tarefas Principais:
        1. [TAREFA 1]
           - [SUBTAREFA 1.1]
           - [SUBTAREFA 1.2]
           - [SUBTAREFA 1.3]
           
        2. [TAREFA 2]
           - [SUBTAREFA 2.1]
           - [SUBTAREFA 2.2]
           - [SUBTAREFA 2.3]
           
        3. [TAREFA 3]
           - [SUBTAREFA 3.1]
           - [SUBTAREFA 3.2]
           - [SUBTAREFA 3.3]
           
        Dicas:
        - [DICA 1]
        - [DICA 2]
        - [DICA 3]
        """
        
        # Converter imagem se houver
        img_data = None
        if image is not None:
            try:
                # Abrir a imagem com PIL
                img = Image.open(image)
                # Criar um buffer para armazenar os dados da imagem
                buffered = io.BytesIO()
                # Salvar a imagem no buffer no formato PNG
                img.save(buffered, format="PNG")
                # Obter os bytes da imagem
                img_bytes = buffered.getvalue()
                # Codificar em base64
                img_data = base64.b64encode(img_bytes).decode('utf-8')
            except Exception as e:
                st.warning(f"Erro ao processar imagem: {str(e)}. Gerando plano sem imagem.")
        
        # Mostrar progresso
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i in range(101):
            time.sleep(0.03)  # Simular processamento
            progress_bar.progress(i)
            status_text.text(f"Gerando plano... {i}%")
        
        # Gerar resposta
        if img_data:
            response = gemini_service.generate_text(formatted_prompt, max_tokens=1024, image=img_data)
        else:
            response = gemini_service.generate_text(formatted_prompt, max_tokens=1024)
        
        # Limpar indicadores de progresso
        progress_bar.empty()
        status_text.empty()
        
        # Salvar resultado
        st.session_state.plan_result = response
    except Exception as e:
        st.error(f"Erro ao gerar plano: {str(e)}")
    finally:
        st.session_state.plan_loading = False

# Função para criar tarefa a partir do plano
def create_tasks_from_plan():
    if not st.session_state.plan_result:
        st.warning("Nenhum plano gerado para criar tarefas")
        return
    
    # Extrair tarefas do plano
    plan_text = st.session_state.plan_result
    
    try:
        # Extrair o título do plano - procurar por linhas numeradas ou seções de título
        lines = plan_text.split('\n')
        title_candidates = []
        
        # Procurar por possíveis linhas de título
        for line in lines:
            line = line.strip()
            # Linhas que parecem ser títulos (não iniciadas por símbolos e com texto significativo)
            if (line and 
                not line.startswith('-') and 
                not line.startswith('*') and 
                not line.startswith('#') and
                len(line) > 5):
                title_candidates.append(line)
        
        # Escolher o título mais adequado
        main_title = "Plano gerado pelo Gemini"
        if title_candidates:
            # Prefira títulos com palavras como "plano", "planejamento", etc.
            for candidate in title_candidates:
                if any(word in candidate.lower() for word in ["plano", "planejamento", "projeto", "tarefa"]):
                    main_title = candidate
                    break
            
            # Se não encontrou nenhum com as palavras-chave, use o primeiro
            if main_title == "Plano gerado pelo Gemini" and title_candidates:
                main_title = title_candidates[0]
        
        # Extrair tarefas principais e subtarefas
        subtask_lines = []
        for i, line in enumerate(lines):
            line = line.strip()
            # Procurar por linhas que começam com '-' ou '*' (marcadores de lista)
            if line.startswith('-') or line.startswith('*'):
                # Remover o marcador e espaços extras
                task_text = line[1:].strip()
                if task_text and len(task_text) > 3:  # Ignorar itens vazios ou muito curtos
                    subtask_lines.append(task_text)
        
        # Procurar também por linhas numeradas (tarefas principais)
        for i, line in enumerate(lines):
            line = line.strip()
            # Padrão "1. Tarefa" ou "1) Tarefa"
            if (line and (line[0].isdigit() and len(line) > 3) and 
                ('.' in line[:3] or ')' in line[:3])):
                task_text = line[line.find('.')+1:].strip() if '.' in line[:3] else line[line.find(')')+1:].strip()
                if task_text and len(task_text) > 3:
                    subtask_lines.append(task_text)
        
        # Limitar a 10 subtarefas
        if len(subtask_lines) > 10:
            subtask_lines = subtask_lines[:10]
        
        # Se não encontrou subtarefas, criar algumas genéricas
        if len(subtask_lines) < 3:
            subtask_lines = [
                "Definir objetivos e requisitos",
                "Coletar recursos necessários",
                "Implementar solução"
            ]
        
        # Criar tarefa com as subtarefas extraídas
        task_service = TaskService()
        result = task_service.add_task_with_subtasks(
            title=main_title,
            subtask_titles=subtask_lines,
            due_date=datetime.now(),
            priority="Média"
        )
        
        if result:
            # Atualizar a contagem de novas tarefas
            if "new_tasks_count" not in st.session_state:
                st.session_state.new_tasks_count = 0
            st.session_state.new_tasks_count += 1
            
            st.success(f"Tarefa '{main_title}' criada com sucesso!")
            return True
        else:
            st.error("Falha ao criar tarefa a partir do plano")
            return False
    except Exception as e:
        st.error(f"Erro ao processar plano: {str(e)}")
        return False

# Página principal de planejamento
def show_planning_page():
    # Inicializar estado da sessão
    init_session_state()
    
    st.header("Planejador com Gemini")
    
    st.markdown("""
    Use a API Gemini para gerar planos detalhados para suas tarefas.
    Descreva o que você precisa planejar e opcionalmente adicione uma imagem para referência.
    """)
    
    # Entrada de texto para o prompt
    st.text_area(
        "Descreva o que você precisa planejar:",
        key="plan_prompt_input",
        height=150,
        placeholder="Ex: Planejar uma viagem para Paris com minha família, incluindo pontos turísticos, hospedagem e transporte.",
        on_change=lambda: setattr(st.session_state, 'plan_prompt', st.session_state.plan_prompt_input)
    )
    
    # Upload de imagem
    uploaded_file = st.file_uploader("Adicionar uma imagem (opcional)", type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
        st.session_state.image_uploaded = uploaded_file
        st.image(uploaded_file, width=300, caption="Imagem carregada")
    
    # Botão para gerar plano
    generate_disabled = st.session_state.plan_loading or not st.session_state.plan_prompt_input
    if st.button("Gerar Plano", disabled=generate_disabled, key="generate_plan_button"):
        # Garantir que o prompt esteja atualizado
        st.session_state.plan_prompt = st.session_state.plan_prompt_input
        generate_plan(st.session_state.plan_prompt, st.session_state.image_uploaded)
    
    # Mostrar loading
    if st.session_state.plan_loading:
        st.info("Gerando plano... Por favor, aguarde.")
    
    # Mostrar resultado do plano abaixo do formulário
    if st.session_state.plan_result:
        st.subheader("Plano Gerado")
        
        # Formatar e exibir o resultado
        st.markdown(st.session_state.plan_result)
        
        # Botão para criar tarefa a partir do plano
        if st.button("Criar Tarefas a partir deste Plano", key="create_tasks_button"):
            success = create_tasks_from_plan()
            if success:
                # Apenas limpar o resultado, não recarregar a página para mostrar mensagem de sucesso
                st.session_state.plan_result = None
                st.rerun()
    else:
        # Instruções exibidas quando não há plano gerado
        st.markdown("""
        ### Como Funciona:
        
        1. **Descreva seu objetivo** na caixa de texto acima
        2. **Clique em "Gerar Plano"** para que a IA crie um plano estruturado
        3. **Revise o plano** gerado que aparecerá aqui
        4. **Clique em "Criar Tarefas"** para converter o plano em tarefas gerenciáveis
        
        As tarefas criadas aparecerão na seção "Suas Tarefas" na página principal.
        """) 