"""
Serviço de análise de imagens usando a API Gemini.
Este módulo processa imagens para análise multimodal com a API Gemini.
"""
import os
import base64
from PIL import Image
import io
from dotenv import load_dotenv
import google.generativeai as genai
from typing import Optional, Dict, Any, Union

# Carregar variáveis de ambiente se não estiverem já carregadas
if "GOOGLE_GENAI_API_KEY" not in os.environ:
    load_dotenv()

class ImageAnalysisService:
    """
    Serviço para processar e analisar imagens usando a API multimodal do Gemini.
    """

    def __init__(self, api_key: Optional[str] = None, debug_mode: bool = False):
        """
        Inicializa o serviço de análise de imagem.

        Args:
            api_key: Chave da API Gemini (opcional, pode usar env var)
            debug_mode: Se deve mostrar informações de debug
        """
        self.debug_mode = debug_mode
        self.api_key = api_key or os.environ.get("GOOGLE_GENAI_API_KEY")

        if not self.api_key:
            raise ValueError("Chave da API Gemini não encontrada. Configure GOOGLE_GENAI_API_KEY.")

        # Configurar o Gemini
        genai.configure(api_key=self.api_key)

    def prepare_image(self, image_path: str = None, image_file = None, max_width: int = 800):
        """
        Prepara uma imagem para envio ao Gemini (redimensiona, converte RGBA para RGB, etc.)

        Args:
            image_path: Caminho para o arquivo de imagem (opcional)
            image_file: Objeto de arquivo de imagem (opcional)
            max_width: Largura máxima para redimensionamento

        Returns:
            bytes: Bytes da imagem processada
        """
        try:
            # Abrir a imagem a partir do caminho ou do objeto de arquivo
            if image_path:
                img = Image.open(image_path)
            elif image_file:
                img = Image.open(image_file)
            else:
                raise ValueError("Nenhuma imagem fornecida")

            # Converter para RGB se for RGBA
            if img.mode == 'RGBA':
                if self.debug_mode:
                    print("Convertendo imagem de RGBA para RGB")
                img = img.convert('RGB')

            # Redimensionar se necessário
            if img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.BICUBIC)
                if self.debug_mode:
                    print(f"Imagem redimensionada para {max_width}x{new_height}")

            # Salvar em buffer como JPEG com qualidade reduzida
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=75)
            img_bytes = buffer.getvalue()

            if self.debug_mode:
                print(f"Tamanho da imagem após processamento: {len(img_bytes)/1024:.2f} KB")

            return img_bytes

        except Exception as e:
            raise Exception(f"Erro ao processar imagem: {str(e)}")

    def analyze_image(self, image_data, prompt: Optional[str] = None):
        """
        Analisa uma imagem usando a API Gemini.

        Args:
            image_data: Bytes da imagem, caminho para o arquivo, ou None para análise somente com texto
            prompt: Prompt personalizado para análise (opcional)

        Returns:
            str: Resultado da análise
        """
        try:
            # Verificar se temos uma imagem ou se é apenas texto
            if image_data is None:
                # Modo somente texto (sem imagem)
                if self.debug_mode:
                    print("Usando modo somente texto (sem imagem)")

                # Carregar o modelo Gemini
                model = genai.GenerativeModel('gemini-1.5-flash')

                # Chamar API apenas com o prompt de texto
                response = model.generate_content(prompt)

                return response.text

            # Caso contrário, processar a imagem normalmente
            # Preparar a imagem se for um caminho
            elif isinstance(image_data, str):
                img_bytes = self.prepare_image(image_path=image_data)
            # Preparar a imagem se for um objeto de arquivo
            elif hasattr(image_data, 'read') and callable(image_data.read):
                img_bytes = self.prepare_image(image_file=image_data)
            # Usar diretamente se já forem bytes
            elif isinstance(image_data, bytes):
                img_bytes = image_data
            else:
                raise ValueError("Formato de imagem não suportado")

            # Usar prompt padrão se não for fornecido
            if not prompt:
                prompt = """
                Analise esta imagem em detalhes e descreva:
                1. O que você vê na imagem
                2. Relevância histórica ou cultural
                3. Detalhes importantes
                4. Elementos notáveis

                Forneça sua análise em português do Brasil.
                """

            # Carregar o modelo Gemini
            model = genai.GenerativeModel('gemini-1.5-flash')

            # Criar conteúdo multimodal
            contents = [
                prompt,
                {
                    "mime_type": "image/jpeg",
                    "data": img_bytes
                }
            ]

            # Chamar API
            response = model.generate_content(contents)

            return response.text

        except Exception as e:
            raise Exception(f"Erro na análise da imagem: {str(e)}")

    def generate_planning_from_image(self, image_data, description: str = ""):
        """
        Gera um plano com base em uma imagem e descrição opcional.

        Args:
            image_data: Imagem para análise
            description: Descrição adicional (opcional)

        Returns:
            str: Plano gerado com base na análise da imagem
        """
        try:
            # Preparar prompt específico para planejamento
            planning_prompt = f"""
            Você é um assistente especializado em organizar tarefas. Com base na imagem e na descrição fornecida,
            crie um plano detalhado com tarefas, subtarefas e um cronograma.

            Descrição adicional: {description}

            Analise a imagem e crie um plano estruturado adequado ao contexto visual apresentado.

            Organize sua resposta no seguinte formato JSON:
            {{
                "titulo": "Título do plano",
                "descricao": "Descrição geral do plano",
                "tarefas": [
                    {{
                        "titulo": "Título da tarefa 1",
                        "descricao": "Descrição detalhada",
                        "prioridade": "alta|média|baixa",
                        "subtarefas": [
                            {{"titulo": "Subtarefa 1.1", "descricao": "Descrição da subtarefa"}}
                        ]
                    }}
                ]
            }}
            """

            # Analisar imagem com o prompt específico
            return self.analyze_image(image_data, prompt=planning_prompt)

        except Exception as e:
            raise Exception(f"Erro ao gerar plano a partir da imagem: {str(e)}")
