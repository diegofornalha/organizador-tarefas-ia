# Resolvendo Conflitos de Configuração em Aplicações Streamlit Modularizadas

## O Problema

Quando desenvolvemos aplicações Streamlit usando uma abordagem modularizada, onde diferentes componentes ou módulos podem ser executados de forma independente ou integrada, é comum encontrar o erro:

```
streamlit.errors.StreamlitSetPageConfigMustBeFirstCommandError: `set_page_config()` can only be called once per app page, and must be called as the first Streamlit command in your script.
```

Este erro ocorre porque o Streamlit impõe duas regras rígidas para a função `st.set_page_config()`:

1. Ela deve ser a **primeira** chamada Streamlit em uma página
2. Ela pode ser chamada **apenas uma vez** por aplicativo

## Princípios da Solução

Para resolver este problema em projetos modularizados, devemos seguir estes princípios:

1. **Separação de preocupações**: Diferenciar código que configura a aplicação do código que implementa funcionalidades
2. **Verificação de contexto**: Executar código de configuração apenas quando necessário
3. **Centralização**: Manter configurações em um único local, preferencialmente no ponto de entrada da aplicação

## Passo a Passo para Resolver o Problema

### 1. Identificar o Contexto de Execução

Determine quando um módulo está sendo executado:
- Como aplicativo principal (`__name__ == "__main__"`)
- Como módulo importado

### 2. Mover Configurações para o Arquivo Principal

Coloque a configuração da página **apenas** no arquivo principal de cada módulo:

```python
# arquivo_principal.py
import streamlit as st

# Verificar se estamos sendo executados como script principal
if __name__ == "__main__":
    # Configuração centralizada (DEVE ser a primeira chamada Streamlit)
    st.set_page_config(
        page_title="Minha Aplicação",
        page_icon="🚀",
        layout="wide"
    )

# Somente após a configuração, importar outros módulos
from meu_modulo import funcao_ui
```

### 3. Remover Configurações de Componentes Reutilizáveis

Nos arquivos de componentes que serão importados, remova qualquer chamada a `st.set_page_config()`:

```python
# componentes.py
import streamlit as st

def minha_interface():
    # NÃO CONFIGURAR A PÁGINA AQUI
    # Implementar apenas a interface, sem configuração
    st.title("Minha Interface")
    st.write("Este componente pode ser usado em qualquer aplicação.")
```

### 4. Usar Portas Diferentes para Módulos Independentes

Quando executar módulos diferentes simultaneamente, use portas diferentes para evitar conflitos:

```bash
# Primeiro módulo (no terminal 1)
streamlit run modulo1/app.py --server.port=8501

# Segundo módulo (no terminal 2)
streamlit run modulo2/app.py --server.port=8502
```

### 5. Gerenciar Scripts de Execução

Crie scripts de execução para facilitar o uso de cada módulo de forma independente:

```bash
#!/bin/bash
# run.sh para um módulo
DIRETORIO="$(dirname "$0")"
cd "$DIRETORIO"
streamlit run app.py --server.port=8501
```

## Exemplo Completo

### Estrutura de Arquivos

```
/meu_projeto/
  /modulo1/
    app.py
    components.py
    run.sh
  /modulo2/
    app.py
    components.py
    run.sh
  /shared/
    utils.py
```

### Arquivo Principal (app.py)

```python
# modulo1/app.py
import streamlit as st

# Configuração APENAS quando executado diretamente
if __name__ == "__main__":
    st.set_page_config(page_title="Módulo 1", page_icon="📊", layout="wide")

# Importações após a configuração
from components import render_ui

# Execução da interface
render_ui()
```

### Arquivo de Componentes (components.py)

```python
# modulo1/components.py
import streamlit as st

def render_ui():
    # SEM configuração de página aqui
    st.title("Interface do Módulo 1")
    
    # Restante da implementação...
```

## Considerações Importantes

1. **Sempre verifique importações**: Certifique-se de que nenhum módulo importado executa `st.set_page_config()`

2. **Cuidado com imports implícitos**: Alguns módulos podem ter código executado na importação, o que pode quebrar a regra da "primeira chamada"

3. **Teste cada módulo independentemente**: Verifique se cada módulo funciona tanto sozinho quanto como parte da aplicação completa

4. **Documente a abordagem**: Deixe comentários explicando onde a configuração está centralizada

## Benefícios Desta Abordagem

- **Modularidade preservada**: Cada módulo pode ser executado de forma independente
- **Reutilização simplificada**: Componentes podem ser compartilhados sem conflitos
- **Manutenção facilitada**: Configurações centralizadas são mais fáceis de ajustar
- **Desenvolvimento paralelo**: Equipes podem trabalhar em módulos diferentes simultaneamente

Seguindo estas regras, suas aplicações Streamlit modularizadas funcionarão sem conflitos de configuração, permitindo uma arquitetura mais flexível e escalável. 
