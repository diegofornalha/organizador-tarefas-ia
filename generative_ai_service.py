"""
Serviço de IA Generativa para o Organizador de Tarefas.
Este módulo fornece interfaces para trabalhar com a API Gemini do Google.
"""
import os
import re
import json
import asyncio
import streamlit as st
from typing import Optional, Dict, Any, List, Union

# Verificar se a biblioteca do Google AI está instalada
try:
    import google.generativeai as genai
    from google.generativeai.types import GenerationConfig
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    print("Biblioteca google.generativeai não encontrada. Algumas funcionalidades serão limitadas.")

class AIService:
    """
    Serviço unificado para integrar APIs de IA generativa com Streamlit.
    Fornece interfaces para trabalhar com Google Gemini e debugging.
    """
    
    def __init__(self, api_key: Optional[str] = None, debug_mode: bool = False):
        """
        Inicializa o serviço de IA.
        
        Args:
            api_key: Chave de API para o Google AI (opcional, pode usar env var)
            debug_mode: Se deve mostrar informações de debug
        """
        self.debug_mode = debug_mode
        
        # Verificar se a API do Google AI está disponível
        if not GENAI_AVAILABLE:
            self._log_error("Biblioteca google.generativeai não instalada. Instale com 'pip install google-generativeai'")
            self.is_initialized = False
            return
            
        # Configurar a chave da API
        self.api_key = api_key or os.environ.get("GOOGLE_GENAI_API_KEY")
        if not self.api_key:
            self._log_warning("⚠️ Chave da API do Google AI não configurada. Algumas funcionalidades podem não funcionar.")
            self.is_initialized = False
            return
        
        # Configurar o GenerativeAI
        self.initialize_genai()
    
    def _log_debug(self, message: str):
        """Registra mensagens de debug apenas se o modo debug estiver ativado."""
        if self.debug_mode:
            st.info(f"🔍 DEBUG: {message}")
            print(f"DEBUG: {message}")
    
    def _log_error(self, message: str):
        """Registra mensagens de erro."""
        st.error(message)
        print(f"ERROR: {message}")
    
    def _log_warning(self, message: str):
        """Registra mensagens de aviso."""
        st.warning(message)
        print(f"WARNING: {message}")
    
    def initialize_genai(self):
        """
        Inicializa a API do Google AI.
        """
        try:
            # Configurar a API do Google
            # Usar método de configuração correto
            genai.configure(api_key=self.api_key)
            
            # Log debug info
            self._log_debug(f"API Gemini inicializada com chave que termina em ...{self.api_key[-4:]}")
            
            self.is_initialized = True
        except Exception as e:
            self._log_error(f"Erro ao inicializar a API do Google AI: {str(e)}")
            self.is_initialized = False
    
    def save_config(self, api_key: str, model: str = "gemini-1.5-flash"):
        """
        Salva a configuração do serviço de IA.
        
        Args:
            api_key: Chave de API para o Google AI
            model: Nome do modelo a ser usado por padrão
        
        Returns:
            bool: True se a configuração foi salva com sucesso
        """
        try:
            # Atualizar a chave API
            self.api_key = api_key
            self.default_model = model
            
            # Reconfigurar a API
            genai.configure(api_key=self.api_key)
            
            # Testar se funciona
            self._log_debug(f"Configuração salva. Modelo padrão: {model}")
            
            self.is_initialized = True
            return True
        except Exception as e:
            self._log_error(f"Erro ao salvar configuração: {str(e)}")
            return False
    
    def create_flow(self, 
                   name: str,
                   prompt_template: str,
                   model: str = "gemini-1.5-flash",
                   temperature: float = 0.7,
                   max_output_tokens: int = 1024,
                   top_p: float = 0.95,
                   top_k: int = 40):
        """
        Cria um fluxo para geração de texto usando o Google AI.
        
        Args:
            name: Nome do fluxo
            prompt_template: Template de prompt com formatação
            model: Nome do modelo a ser usado
            temperature: Temperatura para geração
            max_output_tokens: Número máximo de tokens
            top_p: Parâmetro top_p para geração
            top_k: Parâmetro top_k para geração
            
        Returns:
            Um objeto representando o fluxo configurado
        """
        if not GENAI_AVAILABLE or not self.is_initialized:
            self._log_error("API do Google AI não inicializada corretamente")
            return None
        
        try:
            # Criar a configuração de geração
            generation_config = {
                "temperature": temperature,
                "max_output_tokens": max_output_tokens,
                "top_p": top_p,
                "top_k": top_k
            }
            
            # Log debug info
            self._log_debug(f"Fluxo '{name}' criado com modelo {model}")
            
            # Criar e retornar um objeto de fluxo
            return {
                "name": name,
                "prompt_template": prompt_template,
                "model": model,
                "generation_config": generation_config
            }
        except Exception as e:
            self._log_error(f"Erro ao criar fluxo: {str(e)}")
            return None
    
    def run_flow(self, flow: Dict[str, Any], input_data: Dict[str, Any], with_streaming: bool = False):
        """
        Executa um fluxo para geração de texto.
        
        Args:
            flow: O fluxo configurado
            input_data: Dados para preencher o template de prompt
            with_streaming: Se deve usar streaming para mostrar resultados progressivamente
            
        Returns:
            O texto gerado
        """
        if not GENAI_AVAILABLE or not self.is_initialized or not flow:
            self._log_error("API do Google AI não inicializada ou fluxo inválido")
            return None
        
        try:
            # Log do prompt que será enviado (para debug)
            prompt_template = flow.get("prompt_template", "")
            prompt = prompt_template.format(**input_data)
            self._log_debug(f"Executando fluxo '{flow['name']}' com prompt: {prompt[:100]}...")
            
            # Carregar o modelo
            model_name = flow.get("model", "gemini-1.5-flash")
            model = genai.GenerativeModel(model_name)
            
            # Configurações de geração
            generation_config = flow.get("generation_config", {})
            
            if with_streaming:
                # Usar streaming para mostrar resultados progressivamente
                return self._run_with_streaming(model, prompt, generation_config)
            else:
                # Gerar conteúdo sem streaming
                response = model.generate_content(prompt, generation_config=generation_config)
                return response.text
        except Exception as e:
            self._log_error(f"Erro ao executar fluxo: {str(e)}")
            return f"Erro: {str(e)}"
    
    def _run_with_streaming(self, model, prompt, generation_config):
        """
        Executa a geração com streaming para atualização progressiva.
        
        Args:
            model: Modelo a ser usado
            prompt: Prompt formatado
            generation_config: Configuração para geração
            
        Returns:
            O texto gerado
        """
        placeholder = st.empty()
        full_response = ""
        
        # Iniciar geração com streaming
        for chunk in model.generate_content(
            prompt,
            generation_config=generation_config,
            stream=True
        ):
            try:
                # Extrair texto do chunk
                chunk_text = chunk.text
                
                # Adicionar ao texto completo
                full_response += chunk_text
                
                # Atualizar a visualização
                placeholder.markdown(full_response)
                
                # Log para debugging (apenas porções pequenas para não sobrecarregar)
                if len(chunk_text) < 50:
                    self._log_debug(f"Chunk recebido: {chunk_text}")
            except Exception as e:
                # Ignorar erros específicos de streaming
                pass
        
        return full_response
    
    def generate_task_suggestions(self, description: str, with_streaming: bool = False):
        """
        Gera sugestões de tarefas com base em uma descrição.
        
        Args:
            description: Descrição do projeto ou contexto
            with_streaming: Se deve usar streaming
            
        Returns:
            Lista de sugestões de tarefas
        """
        self._log_debug(f"Gerando sugestões de tarefas para: {description[:50]}...")
        
        prompt_template = """
        Você é um assistente especializado em ajudar a organizar tarefas. 
        Com base na seguinte descrição, sugira uma lista estruturada de tarefas:
        
        {description}
        
        Por favor, retorne a resposta no seguinte formato JSON:
        ```json
        [
          {
            "title": "Título da Tarefa 1",
            "description": "Descrição detalhada",
            "priority": "alta|média|baixa",
            "subtasks": [
              {"title": "Subtarefa 1", "description": "Descrição da subtarefa"}
            ]
          }
        ]
        ```
        """
        
        # Criar fluxo para geração de tarefas
        flow = self.create_flow(
            name="task_suggestion",
            prompt_template=prompt_template,
            model="gemini-1.5-flash",
            temperature=0.7
        )
        
        if not flow:
            return None
        
        # Executar o fluxo
        result = self.run_flow(flow, {"description": description}, with_streaming=with_streaming)
        
        # Processar o resultado (extrair JSON)
        try:
            if not result or not isinstance(result, str):
                self._log_error("Resultado inválido da API Gemini")
                return None
                
            # Extrair JSON do resultado (caso esteja entre codeblocks)
            json_text = result
            if "```json" in result:
                match = re.search(r'```json\s*([\s\S]*?)\s*```', result)
                if match:
                    json_text = match.group(1)
            elif "```" in result:
                match = re.search(r'```\s*([\s\S]*?)\s*```', result)
                if match:
                    json_text = match.group(1)
            
            tasks = json.loads(json_text)
            self._log_debug(f"{len(tasks)} tarefas geradas com sucesso")
            return tasks
        except Exception as e:
            self._log_error(f"Erro ao processar resultado: {str(e)}")
            if isinstance(result, str):
                st.code(result)  # Mostrar o resultado bruto em caso de erro
            return None
    
    # Compatibilidade com o GeminiService
    def generate_text(self, prompt, max_tokens=256, image=None):
        """
        Gera texto a partir de um prompt usando a API Gemini.
        Método de compatibilidade com o GeminiService original.

        Args:
            prompt (str): O prompt para gerar texto
            max_tokens (int, optional): Número máximo de tokens. Defaults to 256.
            image (str, optional): Imagem em base64 para o prompt multimodal. Defaults to None.

        Returns:
            str: O texto gerado
        """
        self._log_debug(f"Gerando texto para prompt: {prompt[:50]}...")
        
        # Criar fluxo simples
        flow = self.create_flow(
            name="text_generation",
            prompt_template="{prompt}",
            model="gemini-1.5-flash" if not image else "gemini-pro-vision",
            max_output_tokens=max_tokens
        )
        
        if not flow:
            return "Erro: Não foi possível criar o fluxo"
        
        # Executar o fluxo
        # Nota: O processamento de imagem precisa ser implementado separadamente
        return self.run_flow(flow, {"prompt": prompt}) 