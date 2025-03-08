# Guia de Manutenção de Módulos

Este documento contém instruções sobre como manter o sistema atualizado quando novos módulos forem adicionados ao projeto.

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
- [ ] Testar se o módulo funciona individualmente
- [ ] Testar se o módulo é iniciado corretamente pelo `run_all.sh`
- [ ] Verificar se o módulo aparece na ordem correta no orquestrador

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
