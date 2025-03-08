# Guia de Manutenção de Módulos

Este documento contém instruções sobre como manter o sistema atualizado quando novos módulos forem adicionados ao projeto.

## Princípio Fundamental: Incorporação e Acoplamento Completo

O princípio mais importante deste sistema é o **acoplamento completo e transparente** entre os módulos. 
Embora a arquitetura seja modular, o objetivo final é proporcionar uma experiência integrada ao usuário, 
onde os módulos funcionem como uma única aplicação coesa. 

### Diretrizes de Incorporação Completa:

- **Transparência para o Usuário**: O usuário não deve perceber fronteiras entre módulos. 
  A navegação entre funcionalidades de diferentes módulos deve ser fluida e natural.
  
- **Integração Visual**: Os componentes de todos os módulos devem manter consistência visual
  e comportamental, independentemente de onde são exibidos.
  
- **Compartilhamento de Estado**: Os módulos devem compartilhar estado de forma eficiente, 
  permitindo que dados gerados em um módulo sejam consumidos por outro sem necessidade de reentrada.
  
- **Carregar e Incorporar**: Não basta que um módulo seja carregado; ele deve ser incorporado 
  na interface principal para que suas funcionalidades centrais estejam disponíveis sem mudança de contexto.
  
- **Fallback Inteligente**: Quando um módulo não está disponível, alternativas inteligentes devem ser 
  oferecidas, preferencialmente com botões para iniciar ou instalar o módulo faltante.

### Indicadores de Incorporação Bem-sucedida:

1. Componentes do módulo são exibidos diretamente na interface principal, e não apenas via links
2. O fluxo de dados entre o módulo e o orquestrador é bidirecional e transparente
3. A experiência do usuário é consistente, independentemente de qual módulo originou cada componente
4. O sistema mantém seu desempenho, mesmo com múltiplos módulos incorporados

Esta filosofia de integração completa é o que diferencia este sistema de uma simples coleção de aplicações 
independentes, transformando-o em uma plataforma verdadeiramente unificada.

## Estrutura Modular do Sistema

O sistema é dividido em módulos independentes que podem ser executados isoladamente ou em conjunto:

- **geral**: Orquestrador central (porta 8510) - Arquivo principal: **implementation.py**
- **plano_tarefas**: Módulo de planejamento e tarefas (porta 8511) - Arquivo principal: **app.py**
- **analise_imagem**: Módulo de análise de imagens (porta 8507) - Arquivo principal: **image_analysis.py**
- **historico_planos**: Módulo de histórico de planos (porta 8512) - Arquivo principal: **app_demo.py**
- **historico_tarefas**: Módulo de histórico de tarefas (porta 8513) - Arquivo principal: **app_demo.py**

Cada módulo tem sua própria porta e arquivo principal para execução.

## Importação de Módulos Locais

Ao criar novos módulos ou arquivos que dependem de importações locais, use o seguinte padrão de importação para garantir que o código funcione tanto isoladamente quanto quando chamado pelo script `run_all.sh`:

```python
# Tentar importar o módulo normalmente
try:
    from nome_do_modulo import funcao1, funcao2
except ImportError:
    # Se falhar, ajustar o sys.path e tentar novamente
    import sys
    import os
    # Adicionar diretório pai ao path
    module_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if module_path not in sys.path:
        sys.path.insert(0, module_path)
    from nome_do_modulo import funcao1, funcao2
```

Este padrão é especialmente importante em arquivos como `app.py` ou `app_demo.py` que podem ser executados de diferentes formas (isoladamente, via script `run.sh` ou via script `run_all.sh`).

## Incorporação de Módulos no Orquestrador Central

Além de permitir que os módulos sejam executados de forma independente, o sistema suporta a incorporação de funcionalidades dos módulos diretamente no orquestrador central (`geral`). Isso melhora a experiência do usuário ao permitir acesso a funcionalidades importantes sem precisar alternar entre diferentes aplicações.

### Padrão de Incorporação

Ao incorporar um módulo no orquestrador central, siga estes passos:

1. **Adicionar importações no `geral/implementation.py`**:
   ```python
   # Import para os componentes do módulo
   sys.path.insert(
       0,
       os.path.join(
           os.path.dirname(os.path.abspath(__file__)),
           "..",
           "servicos_modularizados",
       ),
   )
   try:
       # IMPORTANTE: Sempre use o caminho COMPLETO para evitar erros de importação
       from servicos_modularizados.nome_do_modulo import componente1, componente2, componente3
   except ImportError:
       componente1 = None
       componente2 = None
       componente3 = None
   ```
   
   > **⚠️ ATENÇÃO**: A forma de importação é CRÍTICA para o funcionamento correto da integração. SEMPRE use o caminho qualificado completo com `from servicos_modularizados.nome_do_modulo import ...` em vez de apenas `from nome_do_modulo import ...`. Não ajustar este caminho adequadamente é uma das causas mais comuns de problemas de importação de módulos no orquestrador.

2. **Incorporar na interface apropriada**:
   - Para componentes de barra lateral, adicione na seção `st.sidebar`
   - Para componentes principais, adicione na aba apropriada ou crie uma nova aba
   - Sempre verifique se o componente está disponível antes de usá-lo:
     ```python
     if componente1 is not None:
         componente1(container)
     else:
         st.error("Componente não disponível")
     ```

3. **Manter a navegação para a aplicação completa**:
   - Sempre forneça links para a aplicação completa como fallback
   - Use o dicionário `MODULE_PORTS` para obter a porta correta

### Exemplos de Incorporação

#### Módulo `historico_planos`

O módulo `historico_planos` foi incorporado de duas formas:

1. **Barra lateral**: O componente `show_plans_history_sidebar` é exibido na barra lateral para acesso rápido ao histórico
2. **Aba de histórico**: Uma aba "Histórico de Planos" foi adicionada na seção de Planejamento e Tarefas
3. **Integração com o planejamento**: Quando um plano é criado na aba de Planejamento, ele é automaticamente salvo no histórico

#### Módulo `plano_tarefas`

O módulo `plano_tarefas` foi incorporado como:

1. **Abas de funcionalidade**: O orquestrador incorpora as abas "Planejamento" e "Tarefas"
2. **Integração entre componentes**: Quando um plano é criado na aba de Planejamento, ele é automaticamente disponibilizado para a aba de Tarefas

### Boas Práticas

1. **Não duplique código**: Utilize os componentes exportados pelos módulos em vez de recriar a funcionalidade
2. **Verifique disponibilidade**: Sempre verifique se os componentes estão disponíveis antes de usá-los
3. **Forneça fallbacks**: Ofereça links para a aplicação completa quando um componente não estiver disponível
4. **Mantenha o desacoplamento**: A incorporação deve ser opcional, não obrigatória
5. **Documente dependências**: Se a incorporação criar dependências entre módulos, documente isso claramente

## Integração Completa de Módulos no Orquestrador (Incorporação Total)

Para integrar um módulo completamente ao orquestrador, como ocorre com "plano_tarefas" e "analise_imagem", siga as instruções técnicas a seguir. Esta abordagem garante que o módulo não apenas seja referenciado pelo orquestrador, mas funcione como parte integral da interface principal.

### Passo a Passo para Incorporação Total

1. **Estrutura de Exportação do Módulo**:
   - Defina claramente no arquivo `__init__.py` do módulo quais componentes são exportados:
   ```python
   # Em servicos_modularizados/nome_do_modulo/__init__.py
   from .components import (
       component1,
       component2,
       show_module_panel,  # Componente principal que será exibido em uma aba
   )
   
   # Exponha explicitamente todas as funções/componentes públicos
   __all__ = [
       "component1",
       "component2",
       "show_module_panel",
   ]
   ```

2. **Importação Correta no Orquestrador**:
   - Use o formato qualificado para importações no `implementation.py` para evitar conflitos:
   ```python
   # Em geral/implementation.py
   sys.path.insert(
       0,
       os.path.join(
           os.path.dirname(os.path.abspath(__file__)),
           "..",
           "servicos_modularizados",
       ),
   )
   try:
       from servicos_modularizados.nome_do_modulo import (
           component1,
           component2,
           show_module_panel,
       )
   except ImportError:
       component1 = None
       component2 = None
       show_module_panel = None
   ```

3. **Criação de Abas Dedicadas**:
   - Garanta que o componente principal do módulo seja renderizado em uma aba dedicada:
   ```python
   # Em geral/implementation.py, na seção de criação de abas
   tabs = st.tabs([
       f"{MODULE_ICONS['modulo1']} modulo1",
       f"{MODULE_ICONS['modulo2']} modulo2",
       f"{MODULE_ICONS['nome_do_modulo']} nome_do_modulo",
   ])
   
   # Na seção que processa as abas
   with tabs[2]:  # Índice correspondente à aba do seu módulo
       if show_module_panel is not None:
           show_module_panel()
       else:
           st.error("Componente não disponível. Verifique a instalação do módulo 'nome_do_modulo'.")
           module_port = MODULE_PORTS.get("nome_do_modulo")
           if module_port:
               st.markdown(f"[Abrir aplicação completa](http://localhost:{module_port})")
   ```

4. **Compartilhamento de Estado entre Módulos**:
   - Use o `st.session_state` para compartilhar dados entre os módulos integrados:
   ```python
   # No seu módulo
   def process_data(data):
       if "shared_data" not in st.session_state:
           st.session_state.shared_data = {}
       st.session_state.shared_data["nome_do_modulo_data"] = data
   
   # Em outro módulo que usa os dados
   def use_external_data():
       if "shared_data" in st.session_state and "nome_do_modulo_data" in st.session_state.shared_data:
           data = st.session_state.shared_data["nome_do_modulo_data"]
           # Processar os dados...
   ```

5. **Design de Componentes para Integração**:
   - Sempre desenhe componentes que possam ser usados de forma independente:
   ```python
   def show_module_panel(container=None):
       """
       Exibe o painel principal do módulo.
       
       Args:
           container: Container onde o componente será renderizado (opcional)
                     Se None, renderiza no st global
       """
       # Determinar o contexto de renderização
       ui = container if container else st
       
       # Renderizar o componente
       ui.header(f"{MODULE_ICONS['nome_do_modulo']} nome_do_modulo")
       # Resto da implementação...
   ```

6. **Tratamento de Dependências**:
   - Garanta que todas as dependências do módulo sejam instaladas quando o orquestrador for executado:
   ```python
   # Em servicos_modularizados/nome_do_modulo/requirements.txt
   # Liste todas as dependências específicas do módulo
   
   # Em run_all.sh, adicione a instalação dessas dependências:
   pip install -r servicos_modularizados/nome_do_modulo/requirements.txt
   ```

7. **Testes de Integração**:
   - Crie testes que verifiquem se o módulo funciona tanto isoladamente quanto integrado:
   ```python
   # Em tests/test_integration.py
   def test_module_integration():
       # Simular a importação como feita no orquestrador
       from servicos_modularizados.nome_do_modulo import show_module_panel
       # Verificar se o componente é carregado corretamente
       assert show_module_panel is not None
   ```

### Verificações de Integração Total

Antes de considerar um módulo completamente integrado, verifique:

- [ ] O módulo pode ser importado corretamente pelo orquestrador
- [ ] O componente principal do módulo é exibido em uma aba dedicada
- [ ] A interface do módulo mantém a aparência e comportamento consistentes
- [ ] O estado é compartilhado corretamente entre os componentes
- [ ] Todas as funcionalidades do módulo estão disponíveis na interface integrada
- [ ] O módulo continua funcionando isoladamente sem alterações no código

### Técnicas para Acoplamento Completo

Para garantir que seu módulo esteja completamente acoplado ao orquestrador e ofereça uma experiência verdadeiramente integrada, siga estas técnicas avançadas:

#### 1. Renderização Direta vs. Links

🚫 **Evitar**: Apenas fornecer links para o módulo independente
```python
# Não faça isso como única opção de integração
st.markdown(f"[Abrir módulo](http://localhost:{port})")
```

✅ **Implementar**: Renderizar componentes diretamente na interface 
```python
# Sempre tente renderizar o componente diretamente
if show_module_panel is not None:
    show_module_panel(container)
else:
    # Oferecer link apenas como fallback
    st.markdown(f"[Abrir módulo](http://localhost:{port})")
```

#### 2. Comunicação Bidirecional de Dados

🚫 **Evitar**: Comunicação unidirecional ou ausência de comunicação
```python
# Não faça isso - apenas exibir sem comunicação bidirecional
module_component()
```

✅ **Implementar**: Garantir fluxo de dados em ambas direções
```python
# Estabelecer comunicação bidirecional
result = module_component(data_from_orchestrator)
if result:
    st.session_state.shared_data_for_other_modules = result
```

#### 3. Detecção e Sincronização de Estado

Implementar verificações de sincronização de estado para detectar quando dados foram modificados em outro módulo:

```python
def check_for_updates():
    """Verifica se algum dado relevante foi modificado por outro módulo"""
    last_update = st.session_state.get("last_module_update", {})
    current_data = get_current_data_hash()
    
    if last_update.get("hash") != current_data:
        # Dados foram modificados, atualizar interface
        st.rerun()
    
    # Atualizar registro de última modificação
    st.session_state.last_module_update = {
        "hash": current_data,
        "timestamp": datetime.now().isoformat()
    }
```

#### 4. Ativação Cruzada entre Módulos

Permitir que ações em um módulo disparem comportamentos em outro:

```python
# No módulo A
def trigger_action_in_module_b(data):
    if "module_b_actions" not in st.session_state:
        st.session_state.module_b_actions = []
    
    # Adicionar ação para ser executada pelo módulo B
    st.session_state.module_b_actions.append({
        "action": "process_data",
        "data": data,
        "requested_at": datetime.now().isoformat()
    })
    
# No módulo B
def check_pending_actions():
    if "module_b_actions" in st.session_state and st.session_state.module_b_actions:
        # Processar ações pendentes
        for action in st.session_state.module_b_actions:
            process_action(action)
        
        # Limpar ações processadas
        st.session_state.module_b_actions = []
```

#### 5. Mimetização de Interface

Garantir que componentes se integrem visualmente, adotando o estilo visual do orquestrador:

```python
def adapt_to_orchestrator_style(component_ui):
    # Detectar tema e configurações visuais do orquestrador
    theme = st.session_state.get("orchestrator_theme", "default")
    
    # Aplicar ajustes específicos baseados no tema
    if theme == "dark":
        component_ui.markdown("""
        <style>
        .component-container { background-color: #262730; color: white; }
        </style>
        """, unsafe_allow_html=True)
    
    return component_ui
```

#### 6. Gestão de Ciclo de Vida

Implementar hooks para que o módulo responda adequadamente a eventos do ciclo de vida da aplicação:

```python
def on_module_load():
    """Executado quando o módulo é carregado pelo orquestrador"""
    # Inicializar recursos
    if "module_initialized" not in st.session_state:
        st.session_state.module_initialized = True
        # Carregar dados iniciais, configurar cache, etc.

def on_module_unload():
    """Executado quando o módulo é descarregado"""
    # Limpar recursos, salvar estado, etc.
    if "unsaved_changes" in st.session_state:
        # Salvar alterações pendentes
        save_pending_changes(st.session_state.unsaved_changes)
```

Ao implementar essas técnicas avançadas, seu módulo não apenas será carregado pelo orquestrador, mas será completamente integrado à experiência unificada da plataforma, resultando em uma aplicação coesa e sem fronteiras perceptíveis entre os componentes.

### Problemas Comuns e Soluções

| Problema | Solução |
|----------|---------|
| Componente aparece como "None" | Verifique o caminho de importação. Use o caminho completo a partir de `servicos_modularizados`. |
| Conflito de nomes | Use nomes únicos para componentes ou importe com aliases: `from modulo import component as modulo_component`. |
| Estado não compartilhado | Certifique-se de usar `st.session_state` consistentemente e verificar a existência das chaves antes de acessá-las. |
| Estilos inconsistentes | Mantenha os estilos e formatos consistentes entre módulos e orquestrador. |
| Dependências faltando | Garanta que o `requirements.txt` do módulo inclua todas as dependências e que elas sejam instaladas no ambiente do orquestrador. |

## Ao Adicionar um Novo Módulo

Quando um novo módulo for adicionado ao sistema, siga os passos abaixo para garantir que tudo funcione corretamente:

### 1. Atualize o Script `run_all.sh`

O script `run_all.sh` é responsável por iniciar todos os módulos do sistema em paralelo. Quando adicionar um novo módulo, atualize-o seguindo este padrão:

```bash
# Adicione esta seção no run_all.sh abaixo dos outros módulos
if [ -d "$DIR/servicos_modularizados/nome_do_novo_modulo" ]; then
    iniciar_servico "Nome do Novo Módulo" "$DIR/servicos_modularizados/nome_do_novo_modulo" XXXX "arquivo_principal.py"
fi
```

Onde:
- `nome_do_novo_modulo` é o nome do diretório do novo módulo
- `Nome do Novo Módulo` é o nome descritivo para exibição
- `XXXX` é a porta designada para o novo módulo (escolha uma porta não utilizada, preferencialmente seguindo o padrão 85XX)
- `arquivo_principal.py` é o arquivo principal do módulo (pode ser app.py, app_demo.py, implementation.py, etc.)

### 2. Atualize a Ordem de Exibição no Orquestrador

Edite o arquivo `geral/implementation.py` e atualize a função `custom_sort_key` para incluir o novo módulo na ordem desejada:

```python
def custom_sort_key(m):
    order = {
        "geral": 0,
        "plano_tarefas": 1,
        "analise_imagem": 2,
        "historico_planos": 3,
        "historico_tarefas": 4,
        "nome_do_novo_modulo": 5  # Adicione o novo módulo aqui
    }
    # Retorna a posição definida ou um valor alto para módulos não listados
    return order.get(m, 100)
```

### 3. Adicione o Módulo ao Dicionário de Portas

Ainda no arquivo `geral/implementation.py`, atualize o dicionário `MODULE_PORTS`:

```python
MODULE_PORTS = {
    "plano_tarefas": 8511,
    "analise_imagem": 8507,
    "historico_planos": 8512,
    "historico_tarefas": 8513,
    "geral": 8510,
    "nome_do_novo_modulo": XXXX,  # Adicione o novo módulo aqui
}
```

### 4. Adicione o Ícone do Módulo

Atualize o dicionário `MODULE_ICONS` para definir um ícone para o novo módulo:

```python
MODULE_ICONS = {
    "plano_tarefas": "📋",
    "analise_imagem": "🔍",
    "historico_planos": "📚",
    "historico_tarefas": "📝",
    "geral": "🧩",
    "nome_do_novo_modulo": "🆕",  # Escolha um ícone adequado
}
```

### 5. Atualize a Seção de Links no Script `run_all.sh`

Adicione o link para o novo módulo na seção de saída do script:

```bash
echo "Acessar os serviços:"
echo "- Orquestrador: http://localhost:8510"
echo "- Planejamento e Tarefas: http://localhost:8511"
echo "- Análise de Imagem: http://localhost:8507"
echo "- Histórico de Planos: http://localhost:8512"
echo "- Histórico de Tarefas: http://localhost:8513"
echo "- Nome do Novo Módulo: http://localhost:XXXX"  # Adicione esta linha
```

## Lista de Verificação

Ao adicionar um novo módulo, certifique-se de:

- [ ] Criar o script `run.sh` no diretório do novo módulo
- [ ] Verificar o nome correto do arquivo principal do módulo (app.py, app_demo.py, etc.)
- [ ] Atualizar o script `run_all.sh` para incluir o novo módulo com o arquivo principal correto
- [ ] Definir uma porta única para o módulo (evitar conflitos)
- [ ] Atualizar a ordem de exibição no orquestrador
- [ ] Atualizar os dicionários `MODULE_PORTS` e `MODULE_ICONS`
- [ ] Verificar se as importações de módulos locais usam o padrão de try-except para evitar erros
- [ ] Garantir que o PYTHONPATH está configurado corretamente no script `run.sh`
- [ ] Avaliar se o módulo pode/deve ser incorporado no orquestrador central (geral)
- [ ] Se incorporado, seguir o padrão documentado na seção "Incorporação de Módulos no Orquestrador Central"
- [ ] **IMPORTANTE**: Sempre usar o caminho de importação qualificado completo (`from servicos_modularizados.nome_do_modulo import ...`) para evitar erros de importação quando o módulo for incorporado
- [ ] Testar se o módulo funciona individualmente
- [ ] Testar se o módulo é iniciado corretamente pelo `run_all.sh`
- [ ] Verificar se o módulo aparece na ordem correta no orquestrador

### Verificações de Acoplamento Completo

Para garantir que seu módulo esteja verdadeiramente integrado à plataforma, verifique também:

- [ ] **Renderização Principal**: Componentes principais do módulo são renderizados diretamente na interface do orquestrador, não apenas como links
- [ ] **Componentes Reutilizáveis**: Cada componente do módulo aceita um parâmetro `container` opcional para permitir renderização em diferentes contextos
- [ ] **Consistência Visual**: O módulo segue os mesmos padrões de design e estilo do orquestrador
- [ ] **Estado Compartilhado**: O módulo utiliza `st.session_state` para compartilhar dados com outros módulos
- [ ] **Bidirecionalidade**: As interações no módulo podem afetar outros módulos e vice-versa
- [ ] **Reatividade**: Mudanças em outros módulos são refletidas automaticamente nos componentes deste módulo
- [ ] **Graceful Degradation**: O módulo fornece experiência adequada mesmo quando funcionalidades dependentes não estão disponíveis
- [ ] **Comunicação Inter-módulos**: Implementado sistema para que módulos possam solicitar ações uns aos outros
- [ ] **Ciclo de Vida**: O módulo responde adequadamente aos eventos de inicialização e encerramento do orquestrador
- [ ] **Zero-Configuração**: Usuários não precisam realizar configurações adicionais para que o módulo funcione integrado

## Exemplo de Implementação de Novo Módulo

Para adicionar um novo módulo chamado "estatisticas", você faria:

1. **No `run_all.sh`**:
   ```bash
   if [ -d "$DIR/servicos_modularizados/estatisticas" ]; then
       iniciar_servico "Estatísticas" "$DIR/servicos_modularizados/estatisticas" 8514 "app_estatisticas.py"
   fi
   ```

   Certifique-se de substituir `app_estatisticas.py` pelo nome real do arquivo principal do módulo.

2. **No `implementation.py` (ordem)**:
   ```python
   order = {
       "geral": 0,
       "plano_tarefas": 1,
       "analise_imagem": 2,
       "historico_planos": 3,
       "historico_tarefas": 4,
       "estatisticas": 5
   }
   ```

3. **No `implementation.py` (portas)**:
   ```python
   MODULE_PORTS = {
       # ... outros módulos ...
       "estatisticas": 8514,
   }
   ```

4. **No `implementation.py` (ícones)**:
   ```python
   MODULE_ICONS = {
       # ... outros módulos ...
       "estatisticas": "📊",
   }
   ```

5. **No `run_all.sh` (links)**:
   ```bash
   echo "- Estatísticas: http://localhost:8514"
   ```

Ao seguir estas instruções, você garantirá que todos os módulos sejam inicializados corretamente e apareçam na ordem desejada no orquestrador do sistema. 
