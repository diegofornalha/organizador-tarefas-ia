#!/bin/bash

# Exibindo diretório atual para debug
echo "Diretório atual: $(pwd)"

# Configurando PYTHONPATH para incluir tanto o diretório atual quanto o diretório pai
export PYTHONPATH=$PYTHONPATH:$(pwd):$(pwd)/..
echo "PYTHONPATH: $PYTHONPATH"

echo "===== Iniciando teste dos serviços modularizados ====="

# Executando o script streamlit diretamente, mantendo o PYTHONPATH
streamlit run test_implementation.py --server.port=8505

# Fim do script
