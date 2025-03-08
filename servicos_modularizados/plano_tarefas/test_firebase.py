#!/usr/bin/env python3
"""
Script para testar a integração com o Firestore no módulo plano_tarefas.
Este script verifica se o serviço de armazenamento de tarefas está funcionando
corretamente, tanto no modo online quanto offline.
"""

import os
import sys
from datetime import datetime

# Configurar caminhos para importação
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICES_DIR = os.path.dirname(CURRENT_DIR)
ROOT_DIR = os.path.dirname(SERVICES_DIR)

# Adicionar diretórios ao path
for path in [ROOT_DIR, SERVICES_DIR, CURRENT_DIR]:
    if path not in sys.path:
        sys.path.insert(0, path)

# Importar o serviço de armazenamento
try:
    # Importar diretamente do módulo local
    from firebase_service import TaskStorageService

    print("✅ Serviço de armazenamento importado com sucesso")
except ImportError as e:
    print(f"❌ Erro ao importar serviço de armazenamento: {str(e)}")
    sys.exit(1)

# Inicializar o serviço
task_storage = TaskStorageService()
print(f"Modo offline: {task_storage.is_offline_mode}")


# Função para criar uma tarefa de teste
def criar_tarefa_teste():
    tarefa = {
        "id": "",  # Será preenchido pelo serviço
        "titulo": f"Tarefa de teste {datetime.now().strftime('%H:%M:%S')}",
        "descricao": "Tarefa criada para testar a integração com o Firestore",
        "prioridade": "alta",
        "created_at": datetime.now().isoformat(),
        "completed": False,
        "subtarefas": [
            {
                "id": "",  # Será preenchido pelo serviço
                "titulo": "Subtarefa 1",
                "descricao": "Primeira subtarefa de teste",
                "completed": False,
            },
            {
                "id": "",  # Será preenchido pelo serviço
                "titulo": "Subtarefa 2",
                "descricao": "Segunda subtarefa de teste",
                "completed": True,
            },
        ],
    }
    return tarefa


# Testar a obtenção de tarefas
print("\n1. Obtendo tarefas existentes...")
tarefas = task_storage.get_tasks()
print(f"Encontradas {len(tarefas)} tarefas")

# Testar a criação de uma nova tarefa
print("\n2. Criando uma nova tarefa...")
nova_tarefa = criar_tarefa_teste()
tarefa_id = task_storage.add_task(nova_tarefa)
print(f"Tarefa criada com ID: {tarefa_id}")

# Testar a obtenção de tarefas novamente
print("\n3. Verificando se a tarefa foi adicionada...")
tarefas = task_storage.get_tasks()
print(f"Agora existem {len(tarefas)} tarefas")

# Testar a atualização de uma tarefa
print("\n4. Atualizando a tarefa criada...")
if tarefa_id:
    # Encontrar a tarefa pelo ID
    tarefa_para_atualizar = None
    for t in tarefas:
        if t.get("id") == tarefa_id:
            tarefa_para_atualizar = t
            break

    if tarefa_para_atualizar:
        tarefa_para_atualizar["titulo"] = (
            f"Tarefa atualizada {datetime.now().strftime('%H:%M:%S')}"
        )
        tarefa_para_atualizar["completed"] = True

        # Atualizar a tarefa
        sucesso = task_storage.update_task(tarefa_id, tarefa_para_atualizar)
        print(f"Atualização {'bem-sucedida' if sucesso else 'falhou'}")
    else:
        print("Tarefa não encontrada para atualização")

# Testar a exclusão de uma tarefa
print("\n5. Excluindo a tarefa criada...")
if tarefa_id:
    sucesso = task_storage.delete_task(tarefa_id)
    print(f"Exclusão {'bem-sucedida' if sucesso else 'falhou'}")

# Verificar o estado final
print("\n6. Estado final do armazenamento...")
tarefas = task_storage.get_tasks()
print(f"Existem {len(tarefas)} tarefas no armazenamento")

print("\nTeste concluído!")
