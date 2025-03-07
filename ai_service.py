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
import base64
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Verificar se a biblioteca do Google AI está instalada
try:
    import google.generativeai as genai
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
            if hasattr(genai, 'configure'):
                genai.configure(api_key=self.api_key)
            else:
                # Alternativa se configure não estiver disponível
                os.environ["GOOGLE_API_KEY"] = self.api_key
                self._log_warning("Usando variável de ambiente para configurar API")

            # Log debug info
            if self.api_key and len(self.api_key) > 4:
                self._log_debug(f"API Gemini inicializada com chave que termina em ...{self.api_key[-4:]}")
            else:
                self._log_debug("API Gemini inicializada com chave inválida")

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
            if hasattr(genai, 'configure'):
                genai.configure(api_key=self.api_key)
            else:
                os.environ["GOOGLE_API_KEY"] = self.api_key

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

    def run_flow(self, flow, input_data, with_streaming=False):
        """
        Executa um fluxo de geração com os parâmetros fornecidos.

        Args:
            flow: Fluxo a ser executado (dicionário com configurações)
            input_data: Dados para preencher o prompt template
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

            # Usar método compatível para criar um modelo
            if hasattr(genai, 'GenerativeModel'):
                model = genai.GenerativeModel(model_name)
            else:
                # Fallback para casos onde a API foi atualizada
                self._log_error(f"Método não disponível: GenerativeModel. Use google-generativeai>=0.8.0")
                return None

            # Configurações de geração
            generation_config = flow.get("generation_config", {})

            # Verificar se há imagem nos dados de entrada
            image = input_data.get("image")

            # Processar a imagem automaticamente se necessário
            if image:
                # Tentativa de redimensionar imagem para reduzir o uso de tokens
                try:
                    # Sempre redimensionar imagens para 600KB max
                    processed_image = self._resize_image_if_needed(image, max_size_kb=600)

                    # Verificar se o tamanho foi reduzido
                    if len(processed_image) < len(image):
                        self._log_debug(f"Imagem redimensionada de {len(image)/1024:.1f}KB para {len(processed_image)/1024:.1f}KB")
                        image = processed_image
                    else:
                        self._log_debug(f"Imagem não precisou ser redimensionada: {len(image)/1024:.1f}KB")
                except Exception as e:
                    self._log_warning(f"Erro ao redimensionar imagem: {str(e)}")

            if with_streaming:
                # Usar streaming para mostrar resultados progressivamente
                if image:
                    # Para execução com streaming e imagem
                    return self._run_with_streaming_multimodal(model, prompt, image, generation_config)
                else:
                    # Para execução com streaming sem imagem
                    return self._run_with_streaming(model, prompt, generation_config)
            else:
                # Gerar conteúdo sem streaming
                try:
                    if image:
                        # Criar conteúdo multimodal com texto e imagem
                        content = [prompt, image]
                        response = model.generate_content(content, generation_config=generation_config)
                    else:
                        # Apenas texto
                        response = model.generate_content(prompt, generation_config=generation_config)

                    return response.text
                except Exception as e:
                    error_msg = str(e)
                    self._log_error(f"Erro ao executar modelo: {error_msg}")

                    # Tentar novamente com imagem menor se o erro for sobre tokens
                    if image and ("token" in error_msg.lower() or "limit" in error_msg.lower()):
                        try:
                            self._log_warning("Tentando novamente com imagem ainda menor...")
                            smaller_image = self._resize_image_if_needed(image, max_size_kb=400)
                            content = [prompt, smaller_image]
                            response = model.generate_content(content, generation_config=generation_config)
                            return response.text
                        except Exception as retry_error:
                            self._log_error(f"Erro ao tentar novamente com imagem menor: {str(retry_error)}")
                            return f"Erro: A imagem é muito complexa para processamento. Tente uma imagem mais simples ou menor."

                    return f"Erro: {str(e)}"
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

    def _run_with_streaming_multimodal(self, model, prompt, image, generation_config):
        """
        Executa a geração com streaming para atualização progressiva com imagem.

        Args:
            model: Modelo a ser usado
            prompt: Prompt formatado
            image: Imagem em formato compatível com o modelo
            generation_config: Configuração para geração

        Returns:
            O texto gerado
        """
        placeholder = st.empty()
        full_response = ""

        # Criar conteúdo multimodal
        content = [prompt, image]

        # Iniciar geração com streaming
        try:
            for chunk in model.generate_content(
                content,
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

                except Exception as e:
                    self._log_error(f"Erro ao processar chunk: {str(e)}")

            # Retornar a resposta completa
            return full_response
        except Exception as e:
            self._log_error(f"Erro ao executar streaming com imagem: {str(e)}")
            return f"Erro ao processar imagem: {str(e)}"

    def generate_task_suggestions(self, description: str, with_streaming: bool = False, image: str = None):
        """
        Gera sugestões de tarefas com base em uma descrição.

        Args:
            description: Descrição do projeto ou contexto
            with_streaming: Se deve usar streaming
            image: Imagem em base64 para análise multimodal (opcional)

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
        result = self.run_flow(flow, {"description": description, "image": image}, with_streaming=with_streaming)

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
            model="gemini-1.5-flash",  # Sempre usar gemini-1.5-flash (funciona para texto e imagem)
            max_output_tokens=max_tokens
        )

        if not flow:
            return "Erro: Não foi possível criar o fluxo"

        # Executar o fluxo
        input_data = {"prompt": prompt}

        # Adicionar imagem ao input se fornecida
        if image:
            try:
                # Preparar dados de imagem para o modelo gemini-1.5-flash
                if image is not None:  # Verificação extra para o tipo
                    input_data["image"] = image
            except Exception as e:
                self._log_error(f"Erro ao processar imagem: {str(e)}")

        return self.run_flow(flow, input_data)

    def _resize_image_if_needed(self, img_base64, max_size_kb=800):
        """
        Redimensiona uma imagem em base64 se ela exceder um tamanho máximo.

        Args:
            img_base64: String base64 da imagem
            max_size_kb: Tamanho máximo em KB

        Returns:
            String base64 da imagem redimensionada
        """
        try:
            # Verificar o tamanho atual
            current_size_kb = len(img_base64) / 1024

            # Se já estiver abaixo do limite, retornar como está
            if current_size_kb <= max_size_kb:
                return img_base64

            # Decodificar a imagem
            img_data = base64.b64decode(img_base64)
            img = Image.open(BytesIO(img_data))

            # Converter para RGB se for RGBA
            if img.mode == 'RGBA':
                self._log_debug("Convertendo imagem de RGBA para RGB antes de processar")
                img = img.convert('RGB')

            # Calcular fator de redução para atingir o tamanho desejado
            # Começamos com qualidade 90% e reduzimos até chegar ao tamanho desejado
            quality = 90
            ratio = 1.0

            while current_size_kb > max_size_kb and (quality > 30 or ratio > 0.3):
                # Redimensionar a imagem
                if ratio < 1.0:
                    new_width = int(img.width * ratio)
                    new_height = int(img.height * ratio)
                    resized_img = img.resize((new_width, new_height), Image.LANCZOS)
                else:
                    resized_img = img

                # Converter para JPEG com qualidade reduzida
                buffer = BytesIO()
                resized_img.save(buffer, format="JPEG", quality=quality)

                # Atualizar a imagem em base64
                img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

                # Verificar o novo tamanho
                current_size_kb = len(img_base64) / 1024

                # Ajustar parâmetros para a próxima iteração
                if current_size_kb > max_size_kb:
                    if quality > 30:
                        quality -= 10
                    else:
                        ratio -= 0.1

            self._log_debug(f"Imagem redimensionada de {len(img_base64)/1024:.2f}KB para qualidade={quality}, ratio={ratio:.1f}")
            return img_base64

        except Exception as e:
            self._log_error(f"Erro ao redimensionar imagem: {str(e)}")
            return img_base64

    def _pre_analyze_image(self, img_base64):
        """
        Pré-analisa a imagem usando o modelo Gemini.

        Args:
            img_base64 (str): Imagem em formato base64

        Returns:
            str: Análise da imagem
        """
        try:
            prompt = """
            Analise esta imagem em detalhes e forneça as seguintes informações:

            1. Descrição geral: O que está visível na imagem?
            2. Personagens/Pessoas: Quem são as pessoas presentes, se houver?
            3. Contexto: Qual parece ser o contexto ou situação representada?
            4. Data/Época: Se possível estimar, de qual período histórico é esta imagem?
            5. Elementos importantes: Quais são os elementos mais significativos?
            6. Elementos de texto: Existe algum texto visível na imagem? Transcreva-o.
            7. Significado histórico: Este é um momento ou documento histórico importante?

            Forneça uma análise completa e detalhada que possa ser usada para criar tarefas educacionais.
            """

            # Usar o método existente generate_text para análise de imagem
            response = self.generate_text(prompt=prompt, max_tokens=1024, image=img_base64)

            if response and isinstance(response, str):
                return response
            else:
                self._log_error("Falha ao analisar imagem: resposta vazia ou inválida")
                return "Falha ao analisar imagem. Verifique a conexão com a API Gemini."

        except Exception as e:
            self._log_error(f"Erro na análise da imagem: {str(e)}")
            import traceback
            self._log_error(traceback.format_exc())
            return f"Erro ao analisar imagem: {str(e)}"
