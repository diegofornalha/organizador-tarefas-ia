#!/bin/bash

# Exibindo informações
echo "===================================================="
echo "  ORQUESTRADOR DE MÓDULOS"
echo "===================================================="

# Garantir que estamos no diretório correto
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"
echo "Diretório atual: $(pwd)"

# Configurando PYTHONPATH
PARENT_DIR="$(dirname "$(pwd)")"
ROOT_DIR="$(dirname "$PARENT_DIR")"
SERVICES_DIR="$PARENT_DIR/servicos_modularizados"

# Adicionar todos os diretórios de serviços ao PYTHONPATH
export PYTHONPATH=$ROOT_DIR:$PARENT_DIR:$DIR:$SERVICES_DIR:$PYTHONPATH

# Listar diretórios de serviços para debug
echo "Diretórios de serviços:"
echo "PARENT_DIR: $PARENT_DIR"
echo "SERVICES_DIR: $SERVICES_DIR"
echo "PYTHONPATH: $PYTHONPATH"

# Verificar dependências essenciais
if ! pip list | grep -q "streamlit"; then
    echo "Instalando dependências necessárias..."
    pip install -r requirements.txt
fi

echo "===== Iniciando orquestrador de módulos ====="

# Executando o Streamlit
streamlit run implementation.py --server.port=8510

# Fim do script
