#!/bin/bash

# Exibindo informações
echo "===================================================="
echo "  TESTE DE INTEGRAÇÃO COM FIRESTORE"
echo "===================================================="

# Garantir que estamos no diretório correto
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"
echo "Diretório atual: $(pwd)"

# Configurando PYTHONPATH para incluir diretórios necessários
PARENT_DIR="$(dirname "$(pwd)")"
ROOT_DIR="$(dirname "$PARENT_DIR")"
export PYTHONPATH=$ROOT_DIR:$PARENT_DIR:$DIR:$PYTHONPATH
echo "PYTHONPATH: $PYTHONPATH"

# Verificar dependências essenciais
if ! pip list | grep -q "firebase-admin"; then
    echo "Instalando dependências do Firebase..."
    pip install firebase-admin==6.2.0
fi

echo "===== Executando teste de integração com Firestore ====="

# Executar o script de teste
python test_firebase.py

echo "===== Teste concluído ====="
