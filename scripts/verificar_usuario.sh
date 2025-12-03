#!/bin/bash

# Script para verificar/criar usuário de teste no container

CONTAINER_NAME="maestro-portal"

echo "Verificando se o container está rodando..."
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo "❌ Container $CONTAINER_NAME não está rodando!"
    exit 1
fi

echo "✅ Container está rodando"
echo ""
echo "Criando/verificando usuário de teste..."
echo "Usuário: Opera"
echo "Senha: Opera@2026"
echo ""

docker exec -it "$CONTAINER_NAME" python -c "
from auth import auth_manager

username = 'Opera'
password = 'Opera@2026'
email = 'ti@opera.security'

print('Criando usuário de teste...')
result = auth_manager.create_user(username, password, email)

if result['success']:
    print('✅ Usuário criado com sucesso!')
    print(f'ID: {result.get(\"user_id\")}')
else:
    if 'já existe' in result['message'].lower() or 'already exists' in result['message'].lower():
        print('ℹ️  Usuário já existe. Testando login...')
        login_result = auth_manager.authenticate(username, password)
        if login_result['success']:
            print('✅ Login funcionando corretamente!')
        else:
            print(f'❌ Erro no login: {login_result[\"message\"]}')
    else:
        print(f'❌ Erro: {result[\"message\"]}')
"

