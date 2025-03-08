#!/usr/bin/env python3
"""
Script para verificar a conexão com o Firestore no projeto principal.
Este script tenta importar o FirebaseService do projeto principal e
verificar se a conexão com o Firestore está funcionando.
"""

import os
import sys

# Configurar caminhos para importação
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICES_DIR = os.path.dirname(CURRENT_DIR)
ROOT_DIR = os.path.dirname(SERVICES_DIR)

# Adicionar diretórios ao path
sys.path.insert(0, ROOT_DIR)  # Garantir que o diretório raiz seja o primeiro

print("==================================================")
print("  VERIFICAÇÃO DE CONEXÃO COM FIRESTORE")
print("==================================================")
print(f"Diretório atual: {CURRENT_DIR}")
print(f"Diretório raiz: {ROOT_DIR}")
print("--------------------------------------------------")

# Tentar importar o FirebaseService do projeto principal
try:
    # Importar diretamente do diretório raiz
    import firebase_service
    print(f"✅ Módulo firebase_service importado com sucesso")

    if hasattr(firebase_service, 'FirebaseService'):
        FirebaseService = firebase_service.FirebaseService
        print("✅ Classe FirebaseService encontrada no módulo")

        # Inicializar o serviço
        firebase = FirebaseService()
        print("✅ FirebaseService inicializado")
        print(f"Modo offline: {firebase.is_offline_mode}")

        # Tentar obter tarefas
        try:
            tarefas = firebase.get_tasks()
            print(f"✅ Obtidas {len(tarefas)} tarefas do Firestore")

            # Mostrar algumas informações sobre as tarefas
            if tarefas:
                print("\nPrimeiras 3 tarefas:")
                for i, tarefa in enumerate(tarefas[:3]):
                    titulo = tarefa.get('title', 'Sem título')
                    tarefa_id = tarefa.get('id', 'Sem ID')
                    print(f"  {i+1}. {titulo} (ID: {tarefa_id})")

        except Exception as e:
            print(f"❌ Erro ao obter tarefas: {str(e)}")
    else:
        print("❌ Classe FirebaseService não encontrada no módulo")
        print("Classes disponíveis:")
        for name in dir(firebase_service):
            if not name.startswith('_'):
                print(f"  - {name}")

except ImportError as e:
    print(f"❌ Erro ao importar módulo firebase_service: {str(e)}")
    print("Verifique se o arquivo firebase_service.py existe no diretório raiz.")

    # Listar arquivos no diretório raiz
    print("\nArquivos no diretório raiz:")
    for file in os.listdir(ROOT_DIR):
        if file.endswith('.py'):
            print(f"  - {file}")

print("\n==================================================")
print("  VERIFICAÇÃO CONCLUÍDA")
print("==================================================")
