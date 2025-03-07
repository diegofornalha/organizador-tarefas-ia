import streamlit as st
import os
import base64
from PIL import Image
from datetime import datetime, timedelta
import asyncio
import time
import io
import uuid
import json
import logging
import re

from task_service import TaskService
from firebase_service import FirebaseService
from ai_service import AIService
from task import Task
from servicos_modularizados import add_log, log_error, log_warning, HistoryService

# Função para inicializar o estado da sessão
def init_session_state():
    # Estado para o planejador
    if "plan_prompt" not in st.session_state:
        st.session_state.plan_prompt = ""
    if "plan_result" not in st.session_state:
        st.session_state.plan_result = None
    if "plan_loading" not in st.session_state:
        st.session_state.plan_loading = False
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

    # Garantir que serviços estejam inicializados
    if "services" not in st.session_state:
        from task_service import TaskService
        from firebase_service import FirebaseService
        from ai_service import AIService

        # Inicializar serviços com a chave da API do .env
        import os
        from dotenv import load_dotenv

        # Carregar variáveis de ambiente do .env
        load_dotenv()

        # Obter a chave da API Gemini do .env
        api_key = os.environ.get("GEMINI_API_KEY")

        # Verificar se DEBUG está ativado
        debug_mode = os.environ.get("DEBUG", "False").lower() == "true"

        # Inicializar serviços
        st.session_state.services = {
            "ai": AIService(api_key=api_key, debug_mode=debug_mode),
            "firebase": FirebaseService(),
            "task": TaskService()
        }

# Garantir acesso aos serviços
def get_services():
    """
    Garante que os serviços estejam inicializados antes de acessá-los.
    """
    # Verificar se os serviços já estão inicializados
    if "services" not in st.session_state:
        # Inicializar o estado da sessão (que inclui os serviços)
        init_session_state()

    return st.session_state.services

# Gerar plano usando a API de IA
def generate_plan(prompt, image=None):
    """
    Gera um plano de tarefas com base na descrição fornecida.

    Args:
        prompt: Descrição do plano a ser gerado
        image: Não utilizado mais diretamente - mantido para compatibilidade
    """
    st.session_state.plan_loading = True

    # Usar o serviço de IA da sessão
    services = get_services()
    ai_service = services.get("ai")
    if not ai_service:
        # Criar uma instância temporária se não estiver disponível
        from ai_service import AIService
        ai_service = AIService()

    # Verificar se temos o serviço de análise de imagem
    image_service = st.session_state.get('image_analysis_service')

    # Verificar se devemos usar o serviço modularizado ou não
    use_modular = st.session_state.get('use_modular_service', True)

    # Obter o serviço de histórico, se disponível
    try:
        history_service = HistoryService()
    except Exception:
        history_service = None

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

        # Mostrar progresso
        progress_bar = st.progress(0)
        status_text = st.empty()

        for i in range(101):
            time.sleep(0.01)  # Simular processamento mais rápido
            progress_bar.progress(i)
            status_text.text(f"Gerando plano... {i}%")

        # Gerar resposta (sem imagem)
        response = ai_service.generate_text(formatted_prompt, max_tokens=1024)

        # Limpar indicadores de progresso
        progress_bar.empty()
        status_text.empty()

        # Atualizar o estado da sessão com o resultado
        st.session_state.plan_result = response
        st.session_state.plan_loading = False

        # Registrar no histórico
        if history_service:
            history_service.register_plan_generation(prompt, False)

        return response
    except Exception as e:
        st.error(f"Erro ao gerar plano: {str(e)}")
        # Atualizar o estado da sessão em caso de erro
        st.session_state.plan_loading = False
        return None

# Função para criar tarefa a partir do plano
def create_tasks_from_plan():
    """
    Cria tarefas a partir do plano gerado.
    """
    if "plan_result" not in st.session_state or not st.session_state.plan_result:
        st.error("Não há plano gerado para criar tarefas")
        return

    try:
        # Obter o serviço de tarefas
        services = get_services()
        task_service = services.get("task")

        # Obter o serviço de histórico, se disponível
        try:
            from servicos_modularizados import HistoryService
            history_service = HistoryService()
        except ImportError:
            history_service = None

        plan_text = st.session_state.plan_result

        # Extrair título do plano
        title_candidates = re.findall(r'^(\d+\.\s*)?([^\n]+)', plan_text)
        title_candidates = [t[1].strip() for t in title_candidates if t[1].strip()]

        # Escolher o título mais adequado
        main_title = "Plano gerado pela IA"

        # Procurar por um título que mencione "plano" ou similar
        if title_candidates:
            for title in title_candidates[:3]:  # Apenas nos primeiros candidatos
                lower_title = title.lower()
                if ("plano" in lower_title or "planejamento" in lower_title or
                    "projeto" in lower_title or "organização" in lower_title):
                    main_title = title
                    break

            # Se não encontrou, usar o primeiro
            if main_title == "Plano gerado pela IA" and title_candidates:
                main_title = title_candidates[0]

        # Extrair tarefas principais e suas subtarefas
        task_blocks = re.findall(r'(\d+\.\s*[^\n]+)((?:\s*-\s*[^\n]+\n*)+)', plan_text)

        if not task_blocks:
            st.warning("Não foi possível identificar tarefas no plano gerado")
            return False

        # Criar tarefas e subtarefas
        for task_title, subtasks_text in task_blocks:
            # Limpar título da tarefa
            task_title = task_title.strip()
            if task_title.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')):
                task_title = task_title[2:].strip()

            # Extrair linhas de subtarefas
            subtask_lines = re.findall(r'-\s*([^\n]+)', subtasks_text)
            subtask_lines = [st.strip() for st in subtask_lines if st.strip()]

            # Criar as subtarefas
            subtasks = []
            for subtask_title in subtask_lines:
                subtask = {
                    "id": str(uuid.uuid4()),
                    "title": subtask_title,
                    "completed": False
                }
                subtasks.append(subtask)

            # Criar a tarefa principal
            task = {
                "id": str(uuid.uuid4()),
                "title": task_title,
                "description": main_title,
                "priority": "Normal",
                "completed": False,
                "subtasks": subtasks
            }

            # Adicionar a tarefa
            task_id = task_service.add_task(task)

            # Registrar no histórico
            if history_service and task_id:
                history_service.register_task_creation(task_title, source="plano")

        st.success(f"Tarefas criadas com sucesso a partir do plano: {main_title}")
        st.session_state.scroll_to_tasks = True

        # Remover o plano após criar as tarefas
        st.session_state.plan_result = None
        return True
    except Exception as e:
        st.error(f"Erro ao criar tarefas do plano: {str(e)}")
        return False

def delete_task(task_id):
    """
    Exclui uma tarefa ou subtarefa.

    Args:
        task_id: ID da tarefa ou subtarefa
    """
    # Obter o serviço de tarefas
    services = get_services()
    task_service = services.get("task")

    if not task_service:
        st.error("Serviço de tarefas não disponível")
        return

    try:
        # Excluir tarefa
        result = task_service.delete_task(task_id)

        if result:
            st.success("Tarefa excluída com sucesso!")
            # Recarregar tarefas
            load_tasks()
        else:
            st.error("Não foi possível excluir a tarefa")
    except Exception as e:
        st.error(f"Erro ao excluir tarefa: {str(e)}")

def toggle_task_completed(task_id, current_status):
    # Obter o serviço de tarefas
    services = get_services()
    task_service = services.get("task")

    if not task_service:
        st.error("Serviço de tarefas não disponível")
        return

    try:
        new_status = not current_status

        # Localizar a tarefa e atualizar seu status
        found = False
        for task in st.session_state.tasks:
            if 'maintask' in task and task['maintask'].get("id") == task_id:
                # Formato antigo
                task['maintask']["completed"] = new_status
                result = task_service.update_task(task_id, task)
                found = True
                break
            elif task.get("id") == task_id:
                # Novo formato
                task["completed"] = new_status
                result = task_service.update_task(task_id, task)
                found = True
                break

        if found:
            st.success(f"Tarefa {'concluída' if new_status else 'reaberta'} com sucesso!")
            st.rerun()
        else:
            st.error("Tarefa não encontrada")
    except Exception as e:
        st.error(f"Erro ao atualizar tarefa: {str(e)}")

def complete_subtask(task_id, subtask_id, current_status):
    # Obter o serviço de tarefas
    services = get_services()
    task_service = services.get("task")

    if not task_service:
        st.error("Serviço de tarefas não disponível")
        return

    try:
        new_status = not current_status

        # Localizar a tarefa principal e a subtarefa
        for task in st.session_state.tasks:
            task_found = False

            if 'maintask' in task and task['maintask'].get("id") == task_id:
                # Formato antigo
                main_task = task['maintask']
                task_found = True
            elif task.get("id") == task_id:
                # Novo formato
                main_task = task
                task_found = True

            if task_found:
                # Procurar a subtarefa
                for subtask in task.get("subtasks", []):
                    if subtask.get("id") == subtask_id:
                        # Atualizar o status da subtarefa
                        subtask["completed"] = new_status

                        # Atualizar a tarefa completa
                        task_service.update_task(task_id, task)

                        # Verificar se todas as subtarefas estão concluídas
                        if task.get("subtasks"):
                            all_completed = all(s.get("completed", False) for s in task.get("subtasks", []))

                            # Se todas as subtarefas estiverem concluídas, marcar a tarefa principal também
                            if all_completed:
                                if 'maintask' in task:
                                    task['maintask']["completed"] = True
                                else:
                                    task["completed"] = True

                                task_service.update_task(task_id, task)

                        st.success(f"Subtarefa {'concluída' if new_status else 'reaberta'} com sucesso!")
                        st.rerun()
                        return

        st.warning("Subtarefa não encontrada")
    except Exception as e:
        st.error(f"Erro ao atualizar subtarefa: {str(e)}")

def load_tasks():
    """
    Carrega as tarefas do sistema usando o TaskService.
    """
    # Garantir que os serviços estejam disponíveis
    services = get_services()

    # Obter o serviço de tarefas
    task_service = services.get("task")

    if not task_service:
        st.error("Serviço de tarefas não disponível")
        return

    try:
        # Carregar tarefas
        tasks = task_service.load_tasks()
        st.session_state.tasks = tasks  # Lista de tarefas já no formato adequado
        return tasks
    except Exception as e:
        st.error(f"Erro ao carregar tarefas: {str(e)}")
        return []

def generate_planning_tasks(user_description, image=None, task_service=None):
    """
    Gera um plano de tarefas a partir de uma descrição do usuário usando a API de IA.

    Args:
        user_description: Descrição do projeto ou plano
        image: Imagem enviada pelo usuário (opcional)
        task_service: Instância do serviço de tarefas

    Returns:
        O resultado processado em formato de tarefas
    """
    # Usar o serviço de IA para gerar o plano
    services = get_services()
    ai_service = services.get("ai")
    if not ai_service:
        # Criar uma instância temporária se não estiver disponível
        from ai_service import AIService
        ai_service = AIService()

    # Processar imagem se houver
    img_data = None
    if image is not None:
        # Converter para base64
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        img_data = base64.b64encode(buffered.getvalue()).decode('utf-8')

    # Construir prompt baseado no tipo de entrada
    prompt_base = """
    Você é um assistente especializado em organizar tarefas. Com base nas informações fornecidas,
    crie um plano detalhado com tarefas, subtarefas e um cronograma.

    Informações fornecidas:

    {info}

    Retorne APENAS o JSON a seguir, sem qualquer explicação adicional:

    ```json
    {
        "title": "Título geral do plano",
        "description": "Descrição resumida do plano",
        "tasks": [
            {
                "title": "Título da tarefa 1",
                "description": "Descrição detalhada",
                "priority": "alta|média|baixa",
                "subtasks": [
                    {"title": "Subtarefa 1.1", "description": "Descrição da subtarefa"}
                ]
            }
        ]
    }
    ```
    """

    formatted_prompt = prompt_base.format(info=user_description)

    # Fazer a chamada para o modelo
    start_time = time.time()
    with st.spinner("Gerando plano..."):
        try:
            if img_data:
                # Usar o fluxo de texto com imagem
                response = ai_service.generate_text(formatted_prompt, max_tokens=1024, image=img_data)
            else:
                # Usar o fluxo de texto simples
                response = ai_service.generate_text(formatted_prompt, max_tokens=1024)

            # Log do tempo de resposta
            elapsed_time = time.time() - start_time
            logging.info(f"Tempo de resposta da IA: {elapsed_time:.2f} segundos")
        except Exception as e:
            st.error(f"Erro ao gerar o plano: {str(e)}")
            logging.error(f"Erro na API de IA: {str(e)}")
            return None

    # Processar a resposta
    if not response:
        st.error("Não foi possível gerar um plano. Tente novamente com uma descrição mais detalhada.")
        return None

    # Parsear o JSON da resposta
    try:
        # Tentar extrair JSON da resposta
        json_match = re.search(r'```json(.*?)```', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1).strip()
        else:
            json_str = response.strip()

        # Remover caracteres invisíveis que podem atrapalhar o parsing
        json_str = json_str.replace('\u200b', '')

        # Parsear o JSON
        data = json.loads(json_str)

        # Adicionar ID para cada tarefa e subtarefa
        main_title = "Plano gerado pela IA"
        if "title" in data:
            main_title = data["title"]

        # Backup do título no caso de problemas
        title_candidates = re.findall(r'"title":\s*"([^"]+)"', json_str)
        if main_title == "Plano gerado pela IA" and title_candidates:
            main_title = title_candidates[0]

        # Adicionar data de criação
        data["created_at"] = datetime.now().isoformat()

        return data
    except Exception as e:
        logging.error(f"Erro ao processar resposta da IA: {str(e)}")
        logging.debug(f"Resposta recebida: {response[:500]}...")  # Primeiro 500 chars para debug
        st.error(f"Erro ao processar o plano. Tente novamente. Detalhes: {str(e)}")
        st.code(response)  # Mostrar a resposta bruta para ajudar no debug
        return None

# Função principal da página
def show_home_page():
    # Inicializar estado da sessão
    init_session_state()

    # Garantir acesso aos serviços
    services = get_services()

    # Barra lateral para configurações
    with st.sidebar:
        st.header("Configurações")

        # Configuração da API
        with st.expander("API de IA", expanded=True):
            ai_service = services.get("ai")
            current_api_key = ai_service.api_key if ai_service and hasattr(ai_service, "api_key") else ""
            masked_key = "••••••••" + current_api_key[-4:] if current_api_key and len(current_api_key) > 4 else "Não configurada"

            st.write(f"API Key atual: {masked_key}")

            # Link para gerar chave API
            st.markdown("""
            <div style="margin: 10px 0; padding: 10px; border-radius: 5px; background-color: rgba(70, 130, 180, 0.1); border: 1px solid rgba(70, 130, 180, 0.3);">
                <a href="https://aistudio.google.com/apikey" target="_blank">🔑 Gerar API Key</a>
            </div>
            """, unsafe_allow_html=True)

            new_api_key = st.text_input(
                "Nova Chave API",
                type="password",
                placeholder="Insira nova chave API se necessário"
            )

            model = st.selectbox(
                "Modelo",
                ["gemini-pro", "gemini-pro-vision", "gemini-1.5-flash"],
                index=2
            )

            # Opção para ativar logs de debug
            debug_mode = st.checkbox("Ativar logs de debug", value=False)
            if ai_service and debug_mode != getattr(ai_service, "debug_mode", False):
                ai_service.debug_mode = debug_mode
                st.success("Modo de debug " + ("ativado" if debug_mode else "desativado"))

            if new_api_key and st.button("Atualizar API Key"):
                try:
                    if ai_service and hasattr(ai_service, "save_config"):
                        ai_service.save_config(new_api_key, model)

                        # Atualizar a variável de ambiente também
                        import os
                        os.environ["GEMINI_API_KEY"] = new_api_key

                        # Atualizar a session_state também
                        services["ai"] = ai_service
                        st.session_state.services = services

                        st.success("✅ API key atualizada com sucesso!")
                        st.rerun()
                    else:
                        st.error("Serviço de IA não está disponível")
                except Exception as e:
                    st.error(f"❌ Erro ao atualizar API key: {str(e)}")

        # Status do Sistema
        with st.expander("Status do Sistema", expanded=False):
            firebase_service = services.get("firebase")
            # Status do Firebase
            firebase_status = "Offline (armazenamento local)"
            if firebase_service and not getattr(firebase_service, 'is_offline_mode', True):
                firebase_status = "Online (conectado ao Firestore)"

            st.subheader("Firebase")
            st.info(firebase_status)

            # Status da API de IA
            st.subheader("API de IA")
            if ai_service and hasattr(ai_service, "api_key") and ai_service.api_key:
                st.success("Conectado")
            else:
                st.warning("Chave API não configurada")

    # Título principal do app
    st.title("📋 Organizador de Tarefas com IA")

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

    # SEÇÃO 1: PLANEJADOR
    st.header("🧠 Planejamento")

    # Texto explicativo e formulário de entrada
    st.markdown("""
    Descreva o que você precisa planejar e a IA criará um plano detalhado de tarefas para você.
    """)

    # Entrada de texto para o prompt do plano
    st.text_area(
        "Descreva o que você precisa planejar:",
        key="plan_prompt_input",
        height=120,
        placeholder="Ex: Planejar uma viagem para Paris com minha família, incluindo pontos turísticos, hospedagem e transporte.",
        on_change=lambda: setattr(st.session_state, 'plan_prompt', st.session_state.plan_prompt_input)
    )

    # Botão para gerar plano
    generate_disabled = st.session_state.plan_loading or not st.session_state.plan_prompt_input
    if st.button("Gerar Plano", disabled=generate_disabled, key="generate_plan_button"):
        # Garantir que o prompt esteja atualizado
        st.session_state.plan_prompt = st.session_state.plan_prompt_input
        generate_plan(st.session_state.plan_prompt, None)  # Removemos o upload de imagem

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
        filtered_tasks = []
        for t in st.session_state.tasks:
            # Verificar o formato da tarefa
            if 'maintask' in t:
                # Formato antigo
                if not t["maintask"].get("completed", False):
                    filtered_tasks.append(t)
            else:
                # Novo formato
                if not t.get("completed", False):
                    filtered_tasks.append(t)
    elif selected_view == "Concluídas":
        # Incluir tarefas onde a principal está concluída OU onde pelo menos uma subtarefa está concluída
        filtered_tasks = []
        for t in st.session_state.tasks:
            if 'maintask' in t:
                # Formato antigo
                main_completed = t["maintask"].get("completed", False)
                has_completed_subtasks = any(s.get("completed", False) for s in t.get("subtasks", []))

                if main_completed or has_completed_subtasks:
                    filtered_tasks.append(t)
            else:
                # Novo formato
                main_completed = t.get("completed", False)
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
            show_clear_all_modal()

    with col_complete_all:
        if st.button("✅", help="Completar todas as tarefas"):
            show_complete_all_modal()

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

def show_clear_all_modal():
    """
    Mostra o modal para confirmar a exclusão de todas as tarefas.
    """
    services = get_services()
    task_service = services.get("task")

    if not task_service:
        st.error("Serviço de tarefas não disponível")
        return

    # Modal para confirmar a ação
    with st.expander("Excluir todas as tarefas", expanded=True):
        st.warning("⚠️ Esta ação não pode ser desfeita! Todas as tarefas serão excluídas.")

        if st.button("Confirmar Exclusão", key="confirm_delete_all"):
            try:
                # Excluir cada tarefa
                tasks = task_service.load_tasks()
                for task in tasks:
                    task_id = task.get('id')
                    if task_id:
                        task_service.delete_task(task_id)

                st.success("Todas as tarefas foram excluídas!")
                load_tasks()
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao excluir tarefas: {str(e)}")

def show_complete_all_modal():
    """
    Mostra o modal para confirmar a marcação de todas as tarefas como concluídas.
    """
    services = get_services()
    task_service = services.get("task")

    if not task_service:
        st.error("Serviço de tarefas não disponível")
        return

    # Modal para confirmar a ação
    with st.expander("Marcar todas como concluídas", expanded=True):
        st.info("Todas as tarefas não concluídas serão marcadas como concluídas.")

        if st.button("Confirmar", key="confirm_complete_all"):
            try:
                # Marcar cada tarefa como concluída
                tasks = task_service.load_tasks()
                for task in tasks:
                    if not task.get('completed', False):
                        task['completed'] = True
                        task_service.update_task(task.get('id'), task)

                st.success("Todas as tarefas foram marcadas como concluídas!")
                load_tasks()
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao atualizar tarefas: {str(e)}")
