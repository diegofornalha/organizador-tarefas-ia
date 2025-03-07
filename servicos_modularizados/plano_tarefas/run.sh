#!/bin/bash

# Exibindo informações
echo "===================================================="
echo "  APLICAÇÃO INTEGRADA DE PLANEJAMENTO E TAREFAS"
echo "===================================================="

# Garantir que estamos no diretório correto
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"
echo "Diretório atual: $(pwd)"

# Configurando PYTHONPATH de forma integrada
# Adiciona os diretórios necessários para acessar todos os módulos
PARENT_DIR="$(dirname "$(pwd)")"
ROOT_DIR="$(dirname "$PARENT_DIR")"
PLANEJAMENTO_DIR="$PARENT_DIR/planejamento"
TAREFAS_DIR="$PARENT_DIR/tarefas"
GERAL_DIR="$PARENT_DIR/geral"

export PYTHONPATH=$ROOT_DIR:$PARENT_DIR:$DIR:$PLANEJAMENTO_DIR:$TAREFAS_DIR:$GERAL_DIR:$PYTHONPATH
echo "PYTHONPATH: $PYTHONPATH"

# Verificar dependências essenciais
if ! pip list | grep -q "streamlit"; then
    echo "Instalando dependências necessárias..."
    pip install streamlit python-dotenv google-generativeai Pillow
fi

echo "===== Iniciando aplicação integrada de planejamento e tarefas ====="

# Executando o Streamlit na porta 8511 para evitar conflitos
streamlit run app.py --server.port=8511

# Fim do script
