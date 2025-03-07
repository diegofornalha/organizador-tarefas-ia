import os
import dotenv
import json
from pathlib import Path

# Carregar variáveis de ambiente
dotenv.load_dotenv()

# Configuração do Firebase (será usado apenas em modo offline)
firebase_config = {
    "apiKey": os.getenv("FIREBASE_API_KEY", ""),
    "projectId": os.getenv("FIREBASE_PROJECT_ID", "organizador-tarefas-gemini"),
    "local_mode": True
}

# Chave da API Gemini
gemini_api_key = os.getenv("GEMINI_API_KEY", "AIzaSyAgdDdQ-IUxDvrbZM96dtZ-p26emIOf9Mw")

def validate_config():
    """
    Valida as configurações necessárias para a aplicação funcionar corretamente.
    
    Returns:
        tuple: (is_valid, errors)
    """
    errors = []
    
    # Verificar API Gemini
    if not gemini_api_key:
        errors.append("Gemini API Key não configurada")
    
    return (len(errors) == 0, errors)

# Garantir que o diretório de configuração existe
def ensure_config_dir():
    """Garante que o diretório de configuração existe"""
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)
    
    # Criar arquivo de configuração do Gemini se não existir
    gemini_config_path = config_dir / "gemini_config.json"
    if not gemini_config_path.exists():
        with open(gemini_config_path, "w") as f:
            json.dump({
                "gemini_api": {
                    "api_key": gemini_api_key,
                    "model": "gemini-2.0-flash"
                }
            }, f, indent=2)

# Inicializar configurações
ensure_config_dir() 