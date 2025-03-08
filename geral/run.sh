#!/bin/bash

# Exibindo informações
echo "===================================================="
echo "  SERVIÇO DE ANÁLISE DE IMAGEM"
echo "===================================================="

# Garantir que estamos no diretório correto
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"
echo "Diretório atual: $(pwd)"

# Configurando PYTHONPATH de forma mais simplificada
# Adiciona apenas o diretório raiz do projeto, os serviços modularizados e o módulo de análise
PARENT_DIR="$(dirname "$(pwd)")"
ROOT_DIR="$(dirname "$PARENT_DIR")"
ANALISE_DIR="$PARENT_DIR/analise_imagem"
export PYTHONPATH=$ROOT_DIR:$PARENT_DIR:$DIR:$ANALISE_DIR:$PYTHONPATH
echo "PYTHONPATH: $PYTHONPATH"

# Verificar dependências essenciais
if ! pip list | grep -q "streamlit"; then
    echo "Instalando dependências necessárias..."
    pip install streamlit python-dotenv google-generativeai Pillow
fi

echo "===== Iniciando serviço de análise de imagem ====="

# Executando o Streamlit
streamlit run implementation.py --server.port=8510

# Fim do script
