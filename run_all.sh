#!/bin/bash

# Exibindo informações
echo "===================================================="
echo "  INICIANDO TODOS OS MÓDULOS DO SISTEMA"
echo "===================================================="

# Garantir que estamos no diretório raiz do projeto
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"
echo "Diretório atual: $(pwd)"

# Verificar dependências essenciais
if ! pip list | grep -q "streamlit"; then
    echo "Instalando dependências necessárias..."
    pip install streamlit python-dotenv google-generativeai Pillow
fi

# Função para iniciar um serviço em background
iniciar_servico() {
    echo "Iniciando $1 na porta $3..."
    cd "$2" && streamlit run "$4" --server.port="$3" &
    echo "Serviço $1 iniciado. PID: $!"
    sleep 2 # Pequena pausa para garantir inicialização sequencial
}

# Limpar a tela
clear

echo "===== Iniciando todos os módulos em paralelo ====="

# Iniciar o módulo principal (orquestrador)
iniciar_servico "Orquestrador" "$DIR/geral" 8510 "implementation.py"

# Iniciar o módulo de planejamento e tarefas
iniciar_servico "Planejamento e Tarefas" "$DIR/servicos_modularizados/plano_tarefas" 8511 "app.py"

# Iniciar o módulo de análise de imagem
iniciar_servico "Análise de Imagem" "$DIR/servicos_modularizados/analise_imagem" 8507 "image_analysis.py"

# Iniciar outros módulos, se estiverem disponíveis
if [ -d "$DIR/servicos_modularizados/historico_planos" ]; then
    iniciar_servico "Histórico de Planos" "$DIR/servicos_modularizados/historico_planos" 8512 "app_demo.py"
fi

if [ -d "$DIR/servicos_modularizados/historico_tarefas" ]; then
    iniciar_servico "Histórico de Tarefas" "$DIR/servicos_modularizados/historico_tarefas" 8513 "app_demo.py"
fi

echo ""
echo "===================================================="
echo "  TODOS OS SERVIÇOS INICIADOS"
echo "===================================================="
echo ""
echo "Acessar os serviços:"
echo "- Orquestrador: http://localhost:8510"
echo "- Planejamento e Tarefas: http://localhost:8511"
echo "- Análise de Imagem: http://localhost:8507"
echo "- Histórico de Planos: http://localhost:8512"
echo "- Histórico de Tarefas: http://localhost:8513"
echo ""
echo "Pressione Ctrl+C para encerrar todos os serviços"

# Aguardar entrada do usuário para encerrar
wait
