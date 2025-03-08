# Módulo Geral - Componentes Reutilizáveis

Este módulo contém componentes, funções e classes reutilizáveis que são compartilhados entre os diferentes serviços modularizados.

## Estrutura de Arquivos

- `app_logger.py` - Sistema de logging centralizado
- `image_analysis_service.py` - Serviço de análise de imagens
- `firestore_service.py` - Integração com Firebase/Firestore
- `history_service.py` - Gerenciamento de histórico
- `sidebar_components.py` - Componentes de UI para barras laterais
- `planos_history_component.py` - Componentes para histórico de planos (versão legada)

## Propósito

O objetivo deste módulo é centralizar código comum para:

1. **Evitar duplicação de código** - Os mesmos componentes são utilizados por diferentes serviços
2. **Facilitar manutenção** - Alterações em componentes compartilhados precisam ser feitas em apenas um lugar
3. **Garantir consistência** - Comportamento uniforme entre diferentes módulos

## Como Importar

Para importar funcionalidades deste módulo, utilize:

```python
# Importar funcionalidades específicas
from geral.app_logger import log_success, log_error
from geral.image_analysis_service import ImageAnalysisService

# Tratamento para quando o módulo não está disponível
try:
    from geral.app_logger import log_success, log_error
except ImportError:
    # Funções de fallback para quando o módulo não está disponível
    def log_success(message):
        print(f"SUCCESS: {message}")
    
    def log_error(message):
        print(f"ERROR: {message}")
```

## Migração de geral_whitelabel

Este módulo anteriormente era chamado `geral_whitelabel` e foi renomeado para `geral` para melhor representar seu propósito. Se você encontrar referências a `geral_whitelabel` no código, elas devem ser atualizadas para `geral`.

## Serviços Dependentes

Os seguintes serviços modularizados dependem deste módulo:

- `analise_imagem`
- `plano_tarefas`
- `historico_planos`
- `historico_tarefas`

## Observações

Este módulo não deve ser executado independentemente, ele serve apenas como uma biblioteca de código compartilhado para os outros módulos. Todas as implementações aqui devem ser projetadas para serem reutilizáveis em múltiplos contextos. 
