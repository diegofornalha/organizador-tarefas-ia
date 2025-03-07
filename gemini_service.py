import json
import os
import base64
from io import BytesIO

# Importar biblioteca oficial do Google para Gemini
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    print("Biblioteca google.generativeai não encontrada. Algumas funcionalidades serão limitadas.")

# Importações opcionais
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import streamlit as st
except ImportError:
    # Stub para quando streamlit não estiver disponível
    class StStub:
        def error(self, msg): print(f"ERROR: {msg}")
        def warning(self, msg): print(f"WARNING: {msg}")
        def info(self, msg): print(f"INFO: {msg}")
        def success(self, msg): print(f"SUCCESS: {msg}")
    st = StStub()

from config import gemini_api_key

class GeminiService:
    def __init__(self):
        """
        Inicializa o serviço Gemini.
        """
        self.config_file = os.path.join(os.getcwd(), 'config', 'gemini_config.json')
        self.api_key = gemini_api_key
        self.model_name = "gemini-2.0-flash"  # Modelo padrão (mais rápido)
        
        # Carregar configurações se existirem
        self._load_config()
        
        # Garantir que a chave da API não está vazia
        if not self.api_key:
            self.api_key = "AIzaSyAgdDdQ-IUxDvrbZM96dtZ-p26emIOf9Mw"
            try:
                st.warning("⚠️ Usando chave da API Gemini padrão. Considere configurar sua própria chave nas configurações.")
            except:
                print("⚠️ Usando chave da API Gemini padrão. Considere configurar sua própria chave nas configurações.")
        
        # Configurar API do Google se disponível
        if GENAI_AVAILABLE:
            genai.configure(api_key=self.api_key)
    
    def _load_config(self):
        """
        Carrega configurações da API Gemini do arquivo JSON.
        """
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                
                if "gemini_api" in config:
                    gemini_config = config["gemini_api"]
                    
                    # Atualizar configurações se existirem no arquivo
                    if "api_key" in gemini_config and gemini_config["api_key"]:
                        self.api_key = gemini_config["api_key"]
                    
                    if "model" in gemini_config and gemini_config["model"]:
                        self.model_name = gemini_config["model"]
            except Exception as e:
                print(f"Erro ao carregar configurações da API Gemini: {e}")
    
    def save_config(self, api_key, model="gemini-2.0-flash"):
        """
        Salva configurações da API Gemini no arquivo JSON.
        
        Args:
            api_key (str): Chave da API Gemini
            model (str, optional): Modelo a ser utilizado
        
        Returns:
            bool: True se as configurações foram salvas com sucesso
        """
        try:
            config = {
                "gemini_api": {
                    "api_key": api_key,
                    "model": model
                }
            }
            
            # Criar diretório se não existir
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            # Atualizar as configurações em uso
            self.api_key = api_key
            self.model_name = model
            
            # Atualizar variável de ambiente também
            os.environ["GEMINI_API_KEY"] = api_key
            
            # Reconfigurar API se disponível
            if GENAI_AVAILABLE:
                genai.configure(api_key=api_key)
            
            return True
        except Exception as e:
            print(f"Erro ao salvar configurações da API Gemini: {e}")
            return False
    
    def generate_text(self, prompt, max_tokens=256, image=None):
        """
        Gera texto a partir de um prompt usando a API Gemini.

        Args:
            prompt (str): O prompt para gerar texto
            max_tokens (int, optional): Número máximo de tokens. Defaults to 256.
            image (str, optional): Imagem em base64 para o prompt multimodal. Defaults to None.

        Returns:
            str: O texto gerado
        """
        if not GENAI_AVAILABLE:
            try:
                st.error("Biblioteca google.generativeai não instalada. Instale com 'pip install google-generativeai'")
            except:
                print("Erro: Biblioteca google.generativeai não instalada.")
            return "Erro: Biblioteca não instalada"
        
        try:
            if not self.api_key:
                try:
                    st.error("Chave da API Gemini não configurada")
                except:
                    print("Erro: Chave da API Gemini não configurada")
                return "Erro: Chave da API não configurada"

            # Verificar se a chave parece válida (começa com AIza)
            if not self.api_key.startswith("AIza"):
                try:
                    st.warning("⚠️ A chave da API Gemini não parece válida. Verifique nas configurações.")
                except:
                    print("⚠️ A chave da API Gemini não parece válida.")

            # Escolher o modelo correto (vision se tiver imagem)
            model_name = self.model_name
            if image and "vision" not in model_name:
                # Usar o modelo de visão se imagem for fornecida
                model_name = "gemini-1.5-pro"  # Suporta multimodal
            
            # Criar modelo
            model = genai.GenerativeModel(model_name)
            
            # Configurações de geração
            generation_config = {
                "max_output_tokens": max_tokens,
                "temperature": 0.7,
                "top_p": 0.8,
                "top_k": 40
            }
            
            # Preparar prompt
            if image:
                try:
                    # Usar imagem para multimodal
                    image_parts = [
                        {"text": prompt},
                        {"inline_data": {"mime_type": "image/jpeg", "data": image}}
                    ]
                    response = model.generate_content(image_parts, generation_config=generation_config)
                except Exception as img_error:
                    try:
                        st.warning(f"Erro ao processar imagem: {str(img_error)}. Continuando apenas com texto.")
                    except:
                        print(f"Erro ao processar imagem: {str(img_error)}. Continuando apenas com texto.")
                    response = model.generate_content(prompt, generation_config=generation_config)
            else:
                response = model.generate_content(prompt, generation_config=generation_config)
            
            # Extrair texto da resposta
            return response.text
        
        except Exception as e:
            error_msg = f"Erro ao gerar texto com a API Gemini: {str(e)}"
            try:
                st.error(error_msg)
            except:
                print(error_msg)
            
            # Tentar com outra chave de API se o erro for de autenticação
            if "authentication" in str(e).lower() and self.api_key != "AIzaSyAgdDdQ-IUxDvrbZM96dtZ-p26emIOf9Mw":
                try:
                    try:
                        st.info("🔑 Tentando com a chave da API alternativa...")
                    except:
                        print("🔑 Tentando com a chave da API alternativa...")
                    
                    backup_key = "AIzaSyAgdDdQ-IUxDvrbZM96dtZ-p26emIOf9Mw"
                    old_key = self.api_key
                    self.api_key = backup_key
                    genai.configure(api_key=backup_key)
                    result = self.generate_text(prompt, max_tokens, image)
                    if result and "Erro" not in result:
                        # Se funcionou, salvar a nova chave
                        self.save_config(backup_key, self.model_name)
                        try:
                            st.success("✅ Chave da API alternativa funcionou e foi salva!")
                        except:
                            print("✅ Chave da API alternativa funcionou e foi salva!")
                    self.api_key = old_key
                    genai.configure(api_key=old_key)
                    return result
                except Exception as backup_error:
                    return f"Erro: Falha em ambas as chaves de API. {str(e)}"
            
            return f"Erro: {str(e)}"
    
    def list_available_models(self):
        """
        Lista os modelos Gemini disponíveis.
        
        Returns:
            list: Lista de modelos disponíveis
        """
        if not GENAI_AVAILABLE:
            return []
        
        try:
            models = []
            for model in genai.list_models():
                if "generateContent" in model.supported_generation_methods:
                    models.append({
                        "name": model.name,
                        "display_name": getattr(model, "display_name", model.name)
                    })
            return models
        except Exception as e:
            try:
                st.error(f"Erro ao listar modelos: {str(e)}")
            except:
                print(f"Erro ao listar modelos: {str(e)}")
            return [] 