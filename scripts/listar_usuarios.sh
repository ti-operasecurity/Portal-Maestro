#!/bin/bash

# Script para listar todos os usuários do banco
# Uso: ./listar_usuarios.sh

CONTAINER_NAME="maestro-portal"

# Verificar se container está rodando
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo "❌ Container $CONTAINER_NAME não está rodando!"
    exit 1
fi

echo "📋 LISTA DE USUÁRIOS"
echo "===================="
echo ""

docker exec "$CONTAINER_NAME" python3 << 'PYTHON_SCRIPT'
from auth import auth_manager

try:
    result = auth_manager.supabase.table('maestro_users').select('id, username, email, active, created_at, last_login').order('id').execute()
    
    if not result.data:
        print("Nenhum usuário encontrado.")
    else:
        print(f"Total de usuários: {len(result.data)}")
        print()
        print(f"{'ID':<5} {'Usuário':<20} {'Email':<30} {'Ativo':<8} {'Criado em':<20} {'Último Login':<20}")
        print("-" * 110)
        
        for user in result.data:
            user_id = str(user.get('id', 'N/A'))
            username = user.get('username', 'N/A')[:18]
            email = (user.get('email') or 'N/A')[:28]
            active = '✅ Sim' if user.get('active', True) else '❌ Não'
            created_at = (user.get('created_at') or 'N/A')[:19] if user.get('created_at') else 'N/A'
            last_login = (user.get('last_login') or 'Nunca')[:19] if user.get('last_login') else 'Nunca'
            
            print(f"{user_id:<5} {username:<20} {email:<30} {active:<8} {created_at:<20} {last_login:<20}")
except Exception as e:
    print(f"❌ Erro ao listar usuários: {str(e)}")
    import traceback
    traceback.print_exc()
PYTHON_SCRIPT

