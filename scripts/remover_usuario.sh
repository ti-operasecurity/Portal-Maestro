#!/bin/bash

# Script para remover usuário do banco
# Uso: ./remover_usuario.sh

CONTAINER_NAME="maestro-portal"

# Verificar se container está rodando
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo "❌ Container $CONTAINER_NAME não está rodando!"
    exit 1
fi

echo "🗑️  REMOVER USUÁRIO"
echo "==================="
echo ""

read -p "Digite o nome de usuário a ser removido: " username

if [ -z "$username" ]; then
    echo "❌ Nome de usuário não pode estar vazio!"
    exit 1
fi

echo ""
echo "⚠️  ATENÇÃO: Esta ação não pode ser desfeita!"
read -p "Confirma a remoção do usuário '$username'? (s/N): " confirmar

if [ "$confirmar" != "s" ] && [ "$confirmar" != "S" ]; then
    echo "❌ Operação cancelada"
    exit 0
fi

echo ""
echo "⏳ Removendo usuário..."

docker exec -i "$CONTAINER_NAME" python3 << PYTHON_SCRIPT
import sys
from auth import auth_manager

username = "$username"

try:
    # Verificar se usuário existe
    result = auth_manager.supabase.table('maestro_users').select('id, username').eq('username', username).execute()
    
    if not result.data:
        print(f"❌ Usuário '{username}' não encontrado!")
        sys.exit(1)
    
    user_id = result.data[0]['id']
    
    # Remover usuário
    auth_manager.supabase.table('maestro_users').delete().eq('id', user_id).execute()
    print(f"✅ Usuário '{username}' removido com sucesso!")
    
except Exception as e:
    print(f"❌ Erro: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYTHON_SCRIPT

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Operação concluída com sucesso!"
else
    echo ""
    echo "❌ Erro ao remover usuário"
    exit 1
fi

