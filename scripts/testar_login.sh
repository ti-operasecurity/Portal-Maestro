#!/bin/bash

# Script para testar login diretamente no container

CONTAINER_NAME="maestro-portal"

echo "🔍 Testando autenticação no container..."
echo ""

docker exec "$CONTAINER_NAME" python -c "
from auth import auth_manager
import sys

username = 'Opera'
password = 'Opera@2026'

print('1. Verificando se o usuário existe...')
try:
    # Tentar buscar o usuário
    result = auth_manager.supabase.table('maestro_users').select('id, username, email').eq('username', username).execute()
    if result.data:
        user = result.data[0]
        print(f'   ✅ Usuário encontrado:')
        print(f'      ID: {user[\"id\"]}')
        print(f'      Username: {user[\"username\"]}')
        print(f'      Email: {user.get(\"email\", \"N/A\")}')
    else:
        print(f'   ❌ Usuário \"{username}\" não encontrado no banco!')
        print('   💡 Criando usuário...')
        create_result = auth_manager.create_user(username, password, 'ti@opera.security')
        if create_result['success']:
            print(f'   ✅ Usuário criado com sucesso! ID: {create_result.get(\"user_id\")}')
        else:
            print(f'   ❌ Erro ao criar usuário: {create_result[\"message\"]}')
            sys.exit(1)
except Exception as e:
    print(f'   ❌ Erro ao verificar usuário: {str(e)}')
    sys.exit(1)

print('')
print('2. Testando autenticação...')
try:
    auth_result = auth_manager.authenticate(username, password)
    if auth_result['success']:
        print('   ✅ Login bem-sucedido!')
        print(f'      User ID: {auth_result[\"user\"][\"id\"]}')
        print(f'      Username: {auth_result[\"user\"][\"username\"]}')
    else:
        print(f'   ❌ Falha no login: {auth_result[\"message\"]}')
        print('')
        print('   💡 Possíveis causas:')
        print('      - Senha incorreta')
        print('      - Hash da senha não corresponde')
        print('      - Problema com bcrypt')
        sys.exit(1)
except Exception as e:
    print(f'   ❌ Erro na autenticação: {str(e)}')
    import traceback
    traceback.print_exc()
    sys.exit(1)

print('')
print('✅ Tudo funcionando corretamente!')
"

