import streamlit as st
import os
import base64
from PIL import Image
from datetime import datetime, timedelta
import asyncio
import time
import io
import uuid

from task_service import TaskService
from firebase_service import FirebaseService
from gemini_service import GeminiService
from task import Task

# Função para inicializar o estado da sessão
def init_session_state():
    # Estado para o planejador
    if "plan_prompt" not in st.session_state:
        st.session_state.plan_prompt = ""
    if "plan_result" not in st.session_state:
        st.session_state.plan_result = None
    if "plan_loading" not in st.session_state:
        st.session_state.plan_loading = False
    if "image_uploaded" not in st.session_state:
        st.session_state.image_uploaded = None
    if "scroll_to_tasks" not in st.session_state:
        st.session_state.scroll_to_tasks = False
    if "scroll_to_plan" not in st.session_state:
        st.session_state.scroll_to_plan = False
    
    # Estado para as tarefas
    if "tasks" not in st.session_state:
        st.session_state.tasks = []
    if "is_loading" not in st.session_state:
        st.session_state.is_loading = False
    if "first_load" not in st.session_state:
        st.session_state.first_load = True
    if "new_tasks_count" not in st.session_state:
        st.session_state.new_tasks_count = 0

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
        
        # Definir flag para rolar até o plano gerado
        st.session_state.scroll_to_plan = True
        
    except Exception as e:
        st.error(f"Erro ao gerar plano: {str(e)}")
    finally:
        st.session_state.plan_loading = False

# Função para criar tarefa a partir do plano
def create_tasks_from_plan():
    if not st.session_state.plan_result:
        st.warning("Nenhum plano gerado para criar tarefas")
        return False
    
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
            st.session_state.new_tasks_count += 1
            
            # Definir flag para rolar até a seção de tarefas
            st.session_state.scroll_to_tasks = True
            
            # Limpar a flag de scroll para plano gerado
            st.session_state.scroll_to_plan = False
            
            st.success(f"Tarefa '{main_title}' criada com sucesso!")
            
            # Atualizar lista de tarefas
            load_tasks()
            
            return True
        else:
            st.error("Falha ao criar tarefa a partir do plano")
            return False
    except Exception as e:
        st.error(f"Erro ao processar plano: {str(e)}")
        return False

def delete_task(task_id):
    """
    Exclui uma tarefa ou subtarefa com base no ID fornecido.
    
    Args:
        task_id: ID da tarefa ou subtarefa a ser excluída. Pode ser um ID (string) ou um objeto tarefa.
    """
    # Se for um objeto tarefa, extrair o ID
    if isinstance(task_id, dict) and "maintask" in task_id:
        task_id = task_id["maintask"].get("id", "")
    
    # Verificar se o ID é válido
    if not task_id or not isinstance(task_id, str):
        st.error("ID de tarefa inválido")
        return
    
    task_service = TaskService()
    try:
        # Verifica se é um ID de subtarefa ou de tarefa principal
        # Procurar primeiro nas subtarefas
        for task in st.session_state.tasks:
            maintask = task["maintask"]
            subtasks = task.get("subtasks", [])
            
            # Verificar se o ID está nas subtarefas
            subtask_found = False
            for i, subtask in enumerate(subtasks):
                if subtask.get("id") == task_id:
                    # Encontrou a subtarefa, vamos removê-la
                    subtasks.pop(i)
                    
                    # Atualizar a tarefa principal
                    task_service.update_task(
                        maintask.get("id", ""), 
                        {"subtasks": subtasks}
                    )
                    
                    # Excluir a subtarefa do Firebase também
                    task_service.firebase.delete_document(task_service.collection_name, task_id)
                    
                    # Não mostrar mensagem, apenas recarregar as tarefas
                    load_tasks()
                    subtask_found = True
                    break
            
            if subtask_found:
                return  # Subtarefa foi encontrada e removida
        
        # Se chegou aqui, não é uma subtarefa, então é uma tarefa principal
        result = task_service.delete_task_with_subtasks(task_id)
        if result:
            st.success("Tarefa excluída com sucesso!")
            load_tasks()
        else:
            st.error("Falha ao excluir tarefa")
    
    except Exception as e:
        st.error(f"Erro ao excluir tarefa: {str(e)}")

def toggle_task_completed(task_id, current_status):
    task_service = TaskService()
    try:
        new_status = not current_status
        result = task_service.update_task(task_id, {"completed": new_status})
        
        if result:
            # Atualizar estado local
            for task in st.session_state.tasks:
                if task["maintask"].get("id") == task_id:
                    task["maintask"]["completed"] = new_status
            
            st.success(f"Tarefa {'concluída' if new_status else 'reaberta'} com sucesso!")
            st.rerun()
        else:
            st.error("Falha ao atualizar status da tarefa")
    except Exception as e:
        st.error(f"Erro ao atualizar tarefa: {str(e)}")

def complete_subtask(task_id, subtask_id, current_status):
    task_service = TaskService()
    try:
        new_status = not current_status
        result = task_service.update_task(subtask_id, {"completed": new_status})
        
        if result:
            # Atualizar estado local e verificar se todas subtarefas estão concluídas
            all_subtasks_completed = True
            
            for task in st.session_state.tasks:
                if task["maintask"].get("id") == task_id:
                    # Atualizar a subtarefa atual
                    for subtask in task["subtasks"]:
                        if subtask.get("id") == subtask_id:
                            subtask["completed"] = new_status
                            break
                    
                    # Reordenar subtarefas colocando as completas por último
                    task["subtasks"] = sorted(task["subtasks"], key=lambda x: x.get('completed', False))
                    
                    # Verificar se todas as subtarefas estão concluídas
                    if task["subtasks"]:  # Se existem subtarefas
                        all_subtasks_completed = all(s.get("completed", False) for s in task["subtasks"])
                        
                        # Se todas as subtarefas estiverem concluídas, marcar a tarefa principal também
                        if all_subtasks_completed and not task["maintask"].get("completed", False):
                            # Atualizar a tarefa principal para concluída
                            maintask_id = task["maintask"].get("id", "")
                            if maintask_id:
                                task_service.update_task(maintask_id, {"completed": True})
                                task["maintask"]["completed"] = True
            
            st.rerun()
        else:
            st.error("Falha ao atualizar status da subtarefa")
    except Exception as e:
        st.error(f"Erro ao atualizar subtarefa: {str(e)}")

def load_tasks():
    task_service = TaskService()
    try:
        # Buscar tarefas principais
        main_tasks = task_service.get_all_tasks()
        tasks_with_subtasks = []
        
        # Para cada tarefa principal, buscar suas subtarefas
        for task in main_tasks:
            subtasks = task_service.get_subtasks(task.get("id", ""))
            tasks_with_subtasks.append({
                "maintask": task,
                "subtasks": subtasks
            })
        
        st.session_state.tasks = tasks_with_subtasks
    except Exception as e:
        st.error(f"Erro ao carregar tarefas: {str(e)}")
        st.session_state.tasks = []

# Função principal da página 
def show_home_page():
    # Inicializar estado da sessão
    init_session_state()
    
    # Carregar tarefas na primeira execução
    if st.session_state.first_load:
        load_tasks()
        st.session_state.first_load = False
    
    # Verificar se precisamos rolar para a seção de tarefas
    if st.session_state.scroll_to_tasks:
        # Adicionar JavaScript para rolar até a seção de tarefas
        js = """
        <script>
            // Tentar rolar para a seção de tarefas quando a página carregar
            window.onload = function() {
                // Pequeno atraso para garantir que a página esteja totalmente carregada
                setTimeout(function() {
                    var element = document.getElementById('suas-tarefas');
                    if (element) {
                        element.scrollIntoView({behavior: 'smooth'});
                    }
                }, 500);
            }
            
            // Tenta executar imediatamente também
            (function() {
                setTimeout(function() {
                    var element = document.getElementById('suas-tarefas');
                    if (element) {
                        element.scrollIntoView({behavior: 'smooth'});
                    }
                }, 100);
            })();
        </script>
        """
        st.markdown(js, unsafe_allow_html=True)
        # Resetar o estado de rolagem
        st.session_state.scroll_to_tasks = False
    
    # Adicionar CSS personalizado para melhorar a aparência
    st.markdown("""
    <style>
    .divider {
        margin: 15px 0;
        opacity: 0.2;
        border: 0;
        border-top: 1px solid rgba(255, 255, 255, 0.1);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Título principal do app
    st.title("📋 Organizador de Tarefas com Gemini")
    
    # SEÇÃO 1: PLANEJADOR
    st.header("Planejador de Tarefas")
    
    # Texto explicativo e formulário de entrada
    st.markdown("""
    Descreva o que você precisa planejar e o Gemini criará um plano detalhado de tarefas para você.
    """)
    
    # Entrada de texto para o prompt do plano
    st.text_area(
        "Descreva o que você precisa planejar:",
        key="plan_prompt_input",
        height=120,
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
    
    # Mostrar resultado do plano se existir
    if st.session_state.plan_result:
        # Adicionar marcador para esta seção
        st.markdown('<div id="plano-gerado"></div>', unsafe_allow_html=True)
        
        st.subheader("Plano Gerado")
        
        # Formatar e exibir o resultado
        st.markdown(st.session_state.plan_result)
        
        # Botão para criar tarefa a partir do plano
        if st.button("Criar Tarefas a partir deste Plano", key="create_tasks_button"):
            success = create_tasks_from_plan()
            if success:
                # Limpar o resultado após criar as tarefas
                st.session_state.plan_result = None
                
                # A rolagem acontecerá automaticamente pela verificação da flag no final da função
                st.rerun()
    
    st.markdown("<hr class='divider'/>", unsafe_allow_html=True)
    
    # SEÇÃO 2: LISTA DE TAREFAS
    # Adicionar um marcador para esta seção que podemos usar para navegação
    st.markdown('<div id="suas-tarefas"></div>', unsafe_allow_html=True)
    
    # Cabeçalho com contador
    if st.session_state.new_tasks_count > 0:
        st.header(f"Suas Tarefas ({st.session_state.new_tasks_count})")
        # Resetar contador ao exibir
        st.session_state.new_tasks_count = 0
    else:
        st.header("Suas Tarefas")
    
    # Filtro de visualização com design melhorado
    view_options = ["Todas", "Pendentes", "Concluídas"]
    selected_view = st.radio("Visualizar:", view_options, horizontal=True)
    
    st.markdown("<hr class='divider'/>", unsafe_allow_html=True)
    
    # Filtrar tarefas com base na visualização selecionada
    filtered_tasks = []
    if selected_view == "Pendentes":
        filtered_tasks = [t for t in st.session_state.tasks if not t["maintask"].get("completed", False)]
    elif selected_view == "Concluídas":
        # Incluir tarefas onde a principal está concluída OU onde pelo menos uma subtarefa está concluída
        filtered_tasks = []
        for t in st.session_state.tasks:
            main_completed = t["maintask"].get("completed", False)
            has_completed_subtasks = any(s.get("completed", False) for s in t.get("subtasks", []))
            
            if main_completed or has_completed_subtasks:
                filtered_tasks.append(t)
    else:
        filtered_tasks = st.session_state.tasks
    
    # Exibir tarefas
    if filtered_tasks:
        for i, task in enumerate(filtered_tasks):
            Task.render(
                task,
                f"task_{i}",
                can_delete=True,
                on_delete=delete_task,  # Passamos a função diretamente
                on_tasks_completed_toggle=lambda task: st.rerun()
            )
            
            if i < len(filtered_tasks) - 1:
                st.markdown("<hr style='margin: 10px 0; opacity: 0.1;'>", unsafe_allow_html=True)
    else:
        st.info("Nenhuma tarefa encontrada.")
        
    # Botões de ação
    col_refresh, col_delete_all, col_complete_all = st.columns(3)
    
    with col_refresh:
        if st.button("🔄", help="Recarregar tarefas"):
            load_tasks()
            st.rerun()
    
    with col_delete_all:
        if st.button("🗑️", help="Excluir todas as tarefas"):
            if len(st.session_state.tasks) > 0:
                for task in st.session_state.tasks:
                    task_id = task["maintask"].get("id", "")
                    if task_id:
                        task_service = TaskService()
                        task_service.delete_task_with_subtasks(task_id)
                st.success("Todas as tarefas foram excluídas!")
                load_tasks()
                st.rerun()
            else:
                st.info("Não há tarefas para excluir.")
    
    with col_complete_all:
        if st.button("✅", help="Completar todas as tarefas"):
            if len(st.session_state.tasks) > 0:
                for task in st.session_state.tasks:
                    task_id = task["maintask"].get("id", "")
                    if task_id and not task["maintask"].get("completed", False):
                        task_service = TaskService()
                        task_service.complete_task(task_id)
                st.success("Todas as tarefas foram marcadas como concluídas!")
                load_tasks()
                st.rerun()
            else:
                st.info("Não há tarefas para completar.")
    
    # Adicionar script para rolagem se necessário
    if st.session_state.scroll_to_plan and st.session_state.plan_result:
        # Script para rolar até o plano gerado
        js = """
        <script>
            // Garantir que o DOM esteja carregado
            document.addEventListener('DOMContentLoaded', function() {
                // Encontrar o elemento pelo ID
                var element = document.getElementById('plano-gerado');
                // Rolar até o elemento se ele existir
                if (element) {
                    element.scrollIntoView({behavior: 'smooth'});
                }
            });
            
            // Tenta executar imediatamente se o DOM já estiver carregado
            (function() {
                var element = document.getElementById('plano-gerado');
                if (element) {
                    setTimeout(function() {
                        element.scrollIntoView({behavior: 'smooth'});
                    }, 500);
                }
            })();
        </script>
        """
        st.markdown(js, unsafe_allow_html=True)
        # Não resetamos a flag aqui para que permaneça entre recarregamentos da página

    elif st.session_state.scroll_to_tasks:
        # Script para rolar até a seção de tarefas
        js = """
        <script>
            // Garantir que o DOM esteja carregado
            document.addEventListener('DOMContentLoaded', function() {
                // Encontrar o elemento pelo ID
                var element = document.getElementById('suas-tarefas');
                // Rolar até o elemento se ele existir
                if (element) {
                    element.scrollIntoView({behavior: 'smooth'});
                }
            });
            
            // Tenta executar imediatamente se o DOM já estiver carregado
            (function() {
                var element = document.getElementById('suas-tarefas');
                if (element) {
                    setTimeout(function() {
                        element.scrollIntoView({behavior: 'smooth'});
                    }, 500);
                }
            })();
        </script>
        """
        st.markdown(js, unsafe_allow_html=True)
        # Resetar a flag após usar
        st.session_state.scroll_to_tasks = False 