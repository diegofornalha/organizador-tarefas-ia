import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import os
import sys
import json

# Inicializar o Firebase Admin SDK
cred_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', './firebase-credentials.json')
print(f"Usando credenciais de: {cred_path}")

try:
    cred = credentials.Certificate(cred_path)
    app = firebase_admin.initialize_app(cred)
    print("Firebase inicializado com sucesso")
except ValueError as e:
    # App já inicializado
    print("Firebase já inicializado, usando app existente")
    app = firebase_admin.get_app()

# Acessar o Firestore
db = firestore.client()

# Consultar todas as tarefas
todos_ref = db.collection('todos')
todos = todos_ref.get()

if not todos:
    print("Nenhuma tarefa encontrada no Firestore.")
    sys.exit(0)

print(f"Encontradas {len(list(todos))} tarefas:")
print("-" * 50)

# Exibir cada tarefa
for doc in todos:
    task = doc.to_dict()
    task_id = doc.id
    title = task.get('title', 'Sem título')
    completed = task.get('completed', False)
    subtasks = task.get('subtasks', [])
    
    print(f"Tarefa: {title}")
    print(f"ID: {task_id}")
    print(f"Status: {'Concluída' if completed else 'Pendente'}")
    print(f"Número de subtarefas: {len(subtasks)}")
    
    # Mostrar subtarefas
    if subtasks:
        print("\nSubtarefas:")
        for i, subtask in enumerate(subtasks, 1):
            subtask_title = subtask.get('title', 'Sem título')
            subtask_completed = subtask.get('completed', False)
            print(f"  {i}. {subtask_title} {'✓' if subtask_completed else '○'}")
    
    print("-" * 50) 