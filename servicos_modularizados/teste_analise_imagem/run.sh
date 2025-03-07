#!/bin/bash

# Exibindo informações
echo "===================================================="
echo "  FERRAMENTA ISOLADA DE ANÁLISE DE IMAGEM"
echo "===================================================="
echo "Diretório atual: $(pwd)"

# Configurando PYTHONPATH para incluir apenas os diretórios necessários
export PYTHONPATH=$PYTHONPATH:$(pwd)/../..:$(pwd)/../../..
echo "PYTHONPATH: $PYTHONPATH"

# Verificar dependências
if ! pip list | grep -q "streamlit"; then
    echo "Instalando dependências necessárias..."
    pip install streamlit python-dotenv google-generativeai
fi

echo "===== Iniciando ferramenta isolada de análise de imagem ====="

# Executando o Streamlit em porta própria (isolada)
streamlit run test_image_analysis.py --server.port=8506

# Fim do script
