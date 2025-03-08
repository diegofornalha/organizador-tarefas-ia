# Serviços Modularizados

Este diretório contém os serviços modularizados do Organizador de Tarefas IA, que podem funcionar de forma independente ou integrada.

## Estrutura de Pastas

- **analise_imagem**: Serviço para análise de imagens com IA
- **historico_planos**: Módulo para gerenciamento do histórico de planos
- **historico_tarefas**: Módulo para gerenciamento do histórico de tarefas
- **plano_tarefas**: Aplicação integrada de planejamento e tarefas

## Dependências Compartilhadas

Todos os módulos dependem da pasta `geral` na raiz do projeto, que contém código compartilhado como:
- Sistema de logging
- Serviço de análise de imagens
- Integração com Firestore
- Componentes de UI reutilizáveis

## Como Executar os Módulos

Cada módulo possui um script `run.sh` que pode ser executado independentemente:

```bash
# Executar o módulo de análise de imagem
cd analise_imagem && ./run.sh

# Executar o módulo integrado de planejamento e tarefas
cd plano_tarefas && ./run.sh

# Executar o módulo de histórico de planos
cd historico_planos && ./run.sh

# Executar o módulo de histórico de tarefas
cd historico_tarefas && ./run.sh
```

## Portas Utilizadas

Para evitar conflitos, cada módulo utiliza uma porta diferente:

- **analise_imagem**: Porta 8507
- **plano_tarefas**: Porta 8511
- **historico_planos**: Porta 8512
- **historico_tarefas**: Porta 8513

## Arquitetura

A arquitetura modular permite:

1. **Execução independente**: Cada módulo pode funcionar sozinho
2. **Integração flexível**: Módulos podem ser combinados conforme necessário
3. **Reuso de código**: Componentes comuns são centralizados na pasta `geral`
4. **Manutenção simplificada**: Alterações em um módulo não afetam os outros 
