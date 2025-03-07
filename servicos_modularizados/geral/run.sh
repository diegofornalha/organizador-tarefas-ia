#!/bin/bash

# Exibindo informações
echo "===================================================="
echo "  SERVIÇOS MODULARIZADOS - MÓDULO GERAL"
echo "===================================================="

# Garantir que estamos no diretório correto
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"
echo "Diretório atual: $(pwd)"

# Configurando PYTHONPATH de forma mais completa
# Adiciona o diretório raiz do projeto, os serviços modularizados e o módulo análise_imagem
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

echo "===== Iniciando serviços modularizados - módulo geral ====="

# Executando o Streamlit
streamlit run implementation.py --server.port=8507

# Fim do script
