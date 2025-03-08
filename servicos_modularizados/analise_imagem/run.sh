#!/bin/bash

# Exibindo informações
echo "===================================================="
echo "  SERVIÇO MODULAR DE ANÁLISE DE IMAGEM"
echo "===================================================="

# Garantir que estamos no diretório correto
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"
echo "Diretório atual: $(pwd)"

# Configurando PYTHONPATH de forma mais completa
# Adiciona o diretório raiz do projeto, os serviços modularizados e o módulo geral
PARENT_DIR="$(dirname "$(pwd)")"
ROOT_DIR="$(dirname "$PARENT_DIR")"
export PYTHONPATH=$ROOT_DIR:$PARENT_DIR:$PARENT_DIR/geral:$PYTHONPATH
echo "PYTHONPATH: $PYTHONPATH"

# Verificar dependências essenciais
if ! pip list | grep -q "streamlit"; then
    echo "Instalando dependências necessárias..."
    pip install streamlit python-dotenv google-generativeai Pillow
fi

echo "===== Iniciando serviço de análise de imagem ====="

# Executando o Streamlit com o arquivo de análise de imagem
# Usando porta 8507 para evitar conflitos
streamlit run image_analysis.py --server.port=8507

# Fim do script
