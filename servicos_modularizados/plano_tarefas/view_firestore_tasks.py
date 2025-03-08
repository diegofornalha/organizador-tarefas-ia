#!/usr/bin/env python3
"""
Script para visualizar as tarefas armazenadas no Firestore.
Este script se conecta diretamente ao Firestore e mostra todas as tarefas
armazenadas, sem depender da aplicação Streamlit.
"""

import os
import sys
import json
from datetime import datetime

# Configurar caminhos para importação
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICES_DIR = os.path.dirname(CURRENT_DIR)
ROOT_DIR = os.path.dirname(SERVICES_DIR)

# Caminho para o arquivo de credenciais
CREDENTIALS_PATH = os.path.join(ROOT_DIR, "firebase-config", "firebase-credentials.json")

# Adicionar diretórios ao path
for path in [ROOT_DIR, SERVICES_DIR, CURRENT_DIR]:
    if path not in sys.path:
        sys.path.insert(0, path)

print("==================================================")
print("  VISUALIZADOR DE TAREFAS NO FIRESTORE")
print("==================================================")

# Verificar se o arquivo de credenciais existe
if not os.path.exists(CREDENTIALS_PATH):
    print(f"❌ Arquivo de credenciais não encontrado: {CREDENTIALS_PATH}")
    sys.exit(1)

try:
    # Importar bibliotecas do Firebase
    import firebase_admin
    from firebase_admin import credentials, firestore

    # Inicializar Firebase
    if not firebase_admin._apps:
        cred = credentials.Certificate(CREDENTIALS_PATH)
        app = firebase_admin.initialize_app(cred)

    # Obter referência ao Firestore
    db = firestore.client()

    # Obter todas as tarefas
    tarefas_ref = db.collection('todos')
    tarefas_docs = tarefas_ref.get()

    # Converter para lista de dicionários
    tarefas = []
    for doc in tarefas_docs:
        tarefa = doc.to_dict()
        tarefa['id'] = doc.id
        tarefas.append(tarefa)

    # Mostrar tarefas
    print(f"\nEncontradas {len(tarefas)} tarefas no Firestore:\n")

    if not tarefas:
        print("Nenhuma tarefa encontrada.")
    else:
        for i, tarefa in enumerate(tarefas, 1):
            # Títulos e informações básicas
            titulo = tarefa.get('titulo', tarefa.get('title', 'Sem título'))
            status = "✅ Concluída" if tarefa.get('completed', False) else "⬜️ Pendente"
            criacao = tarefa.get('created_at', 'Data desconhecida')

            # Formatar data de criação se possível
            try:
                if "T" in criacao:
                    dt = datetime.fromisoformat(criacao)
                    criacao = dt.strftime("%d/%m/%Y %H:%M")
            except:
                pass

            # Mostrar informações da tarefa
            print(f"{i}. {titulo} [{status}]")
            print(f"   ID: {tarefa['id']}")
            print(f"   Criação: {criacao}")

            # Mostrar descrição se existir
            descricao = tarefa.get('descricao', tarefa.get('description', ''))
            if descricao:
                # Limitar a 100 caracteres e adicionar "..." se for mais longo
                if len(descricao) > 100:
                    descricao = descricao[:97] + "..."
                print(f"   Descrição: {descricao}")

            # Mostrar subtarefas se existirem
            subtarefas = tarefa.get('subtarefas', tarefa.get('subtasks', []))
            if subtarefas:
                print(f"   Subtarefas ({len(subtarefas)}):")
                for j, sub in enumerate(subtarefas, 1):
                    sub_status = "✅" if sub.get('completed', False) else "⬜️"
                    sub_titulo = sub.get('titulo', sub.get('title', 'Sem título'))
                    print(f"      {j}. {sub_status} {sub_titulo}")

            print("   " + "-" * 40)

except ImportError as e:
    print(f"❌ Erro ao importar bibliotecas do Firebase: {str(e)}")
    print("Verifique se o firebase-admin está instalado:")
    print("pip install firebase-admin==6.2.0")

except Exception as e:
    print(f"❌ Erro ao acessar o Firestore: {str(e)}")

print("\n==================================================")
print("  VISUALIZAÇÃO CONCLUÍDA")
print("==================================================")
