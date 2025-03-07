#!/bin/bash

# Exibindo informações
echo "===================================================="
echo "  SERVIÇO MODULAR DE PLANEJAMENTO"
echo "===================================================="

# Garantir que estamos no diretório correto
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"
echo "Diretório atual: $(pwd)"

# Configurando PYTHONPATH de forma mais completa
# Adiciona o diretório raiz do projeto, os serviços modularizados e o módulo geral
PARENT_DIR="$(dirname "$(pwd)")"
ROOT_DIR="$(dirname "$PARENT_DIR")"
GERAL_DIR="$PARENT_DIR/geral"
export PYTHONPATH=$ROOT_DIR:$PARENT_DIR:$DIR:$GERAL_DIR:$PYTHONPATH
echo "PYTHONPATH: $PYTHONPATH"

# Verificar dependências essenciais
if ! pip list | grep -q "streamlit"; then
    echo "Instalando dependências necessárias..."
    pip install streamlit python-dotenv google-generativeai Pillow
fi

echo "===== Iniciando serviço de planejamento ====="

# Executando o Streamlit com o arquivo de planejamento
# Usando porta 8508 para evitar conflitos
streamlit run planning.py --server.port=8508

# Fim do script
