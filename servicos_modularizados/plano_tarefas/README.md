# Módulo Plano-Tarefas

Este módulo integra as funcionalidades de criação de planos e gerenciamento de tarefas.

## Funcionalidades

- **Criação de Planos**: Permite criar planos estruturados com tarefas e subtarefas.
- **Gerenciamento de Tarefas**: Interface para visualizar, editar, concluir e excluir tarefas.
- **Persistência no Firestore**: Integração com o Firebase/Firestore para armazenamento persistente de tarefas.

## Componentes Principais

### `app.py`
Aplicação principal que integra os componentes de planejamento e tarefas.

### `planejamento_components.py`
Componentes para a criação e geração de planos.

### `tarefas_components.py`
Componentes para o gerenciamento de tarefas, incluindo criação, exibição, edição e exclusão.

### `firebase_service.py`
Serviço de integração com o Firestore, que permite persistência de dados entre sessões:

- Se o serviço Firestore estiver disponível na aplicação principal, as tarefas serão sincronizadas com o banco de dados.
- Se o Firestore não estiver disponível, o módulo tentará inicializar uma conexão direta com o Firestore usando as credenciais locais.
- Se nenhuma das opções funcionar, as tarefas ficarão apenas na sessão local do Streamlit.

## Integração com o Projeto Principal

### Como o módulo se integra com o Firestore

1. O módulo tenta importar o `FirebaseService` da aplicação principal.
2. Se a importação for bem-sucedida, todas as operações de tarefas (criar, atualizar, excluir) serão sincronizadas com o Firestore.
3. Se a importação falhar, o módulo tenta inicializar sua própria conexão com o Firestore usando o arquivo de credenciais em `firebase-config/firebase-credentials.json`.
4. Se não conseguir conectar ao Firestore, o módulo continua funcionando com armazenamento local utilizando `st.session_state`.

### Configuração do Firebase

O módulo requer um arquivo de credenciais do Firebase para funcionar no modo online. O arquivo deve estar localizado em:

```
/firebase-config/firebase-credentials.json
```

Este arquivo contém as credenciais de acesso ao projeto Firebase e é essencial para a conexão com o Firestore.

### Fluxo de Dados

```
[Interface do Usuário] <-> [tarefas_components.py] <-> [firebase_service.py] <-> [Firestore/Local Storage]
```

## Uso

Para executar o módulo independentemente:

```bash
cd servicos_modularizados/plano_tarefas
python app.py
```

Ou usando o script de execução:

```bash
cd servicos_modularizados/plano_tarefas
./run.sh
```

Para integrar com a aplicação principal, importe os componentes necessários:

```python
from servicos_modularizados.plano_tarefas.tarefas_components import tasks_ui, criar_tarefas_do_plano
from servicos_modularizados.plano_tarefas.planejamento_components import planning_ui
```

## Testes e Ferramentas

### Teste de Integração com Firestore

Para testar a integração com o Firestore, execute o script de teste:

```bash
cd servicos_modularizados/plano_tarefas
./test_firebase.sh
```

Este script verifica:
1. A conexão com o serviço Firestore
2. A criação de tarefas
3. A atualização de tarefas
4. A exclusão de tarefas
5. A recuperação de tarefas

O teste funciona tanto no modo online (com Firestore) quanto no modo offline (armazenamento local).

### Visualizador de Tarefas no Firestore

Para visualizar as tarefas armazenadas no Firestore, execute:

```bash
cd servicos_modularizados/plano_tarefas
python view_firestore_tasks.py
```

Este script mostra todas as tarefas armazenadas no Firestore, incluindo:
- Título e status (concluída/pendente)
- ID da tarefa
- Data de criação
- Descrição
- Subtarefas (se existirem)

### Verificação da Conexão com o Projeto Principal

Para verificar a conexão com o serviço Firebase do projeto principal:

```bash
cd servicos_modularizados/plano_tarefas
python check_root_firebase.py
```

Este script tenta importar o `FirebaseService` do projeto principal e verificar se a conexão está funcionando.

## Estrutura de Dados

### Tarefa

```json
{
  "id": "unique-id",
  "titulo": "Título da Tarefa",
  "descricao": "Descrição detalhada",
  "prioridade": "alta|média|baixa",
  "completed": false,
  "created_at": "2023-07-01T10:30:00.000Z",
  "subtarefas": [
    {
      "id": "subtask-id",
      "titulo": "Subtarefa 1",
      "descricao": "Descrição da subtarefa",
      "completed": false
    }
  ]
}
```

## Requisitos

- Python 3.8+
- Streamlit
- Firebase Admin SDK (para persistência no Firestore)
- Arquivo de credenciais do Firebase 
