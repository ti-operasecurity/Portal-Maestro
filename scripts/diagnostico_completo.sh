#!/bin/bash

# Script completo de diagnóstico e correção

CONTAINER_NAME="maestro-portal"

echo "🔍 DIAGNÓSTICO COMPLETO DO SISTEMA DE AUTENTICAÇÃO"
echo "=================================================="
echo ""

# 1. Verificar container
echo "1️⃣ Verificando container..."
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo "   ❌ Container não está rodando!"
    exit 1
fi
echo "   ✅ Container está rodando"
echo ""

# 2. Verificar variáveis de ambiente
echo "2️⃣ Verificando variáveis de ambiente..."
docker exec "$CONTAINER_NAME" python -c "
import os
url = os.getenv('SUPABASE_URL', '')
key = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')
secret = os.getenv('SECRET_KEY', '')

print(f'   SUPABASE_URL: {\"✅ definida\" if url else \"❌ não definida\"} (tamanho: {len(url)})')
print(f'   SUPABASE_SERVICE_ROLE_KEY: {\"✅ definida\" if key else \"❌ não definida\"} (tamanho: {len(key)})')
print(f'   SECRET_KEY: {\"✅ definida\" if secret else \"❌ não definida\"} (tamanho: {len(secret)})')

if '\\r' in url or '\\r' in key:
    print('   ⚠️  AVISO: Caracteres \\r encontrados nas variáveis!')
"
echo ""

# 3. Verificar conexão com Supabase
echo "3️⃣ Testando conexão com Supabase..."
docker exec "$CONTAINER_NAME" python -c "
from auth import auth_manager
try:
    # Tenta fazer uma query simples
    result = auth_manager.supabase.table('maestro_users').select('count').execute()
    print('   ✅ Conexão com Supabase OK')
except Exception as e:
    print(f'   ❌ Erro na conexão: {str(e)}')
    exit(1)
"
echo ""

# 4. Verificar/criar usuário
echo "4️⃣ Verificando usuário de teste..."
docker exec "$CONTAINER_NAME" python -c "
from auth import auth_manager

username = 'Opera'
password = 'Opera@2026'
email = 'ti@opera.security'

# Verificar se existe
result = auth_manager.supabase.table('maestro_users').select('id, username, email, active').eq('username', username).execute()

if result.data:
    user = result.data[0]
    print(f'   ✅ Usuário encontrado:')
    print(f'      ID: {user[\"id\"]}')
    print(f'      Username: {user[\"username\"]}')
    print(f'      Email: {user.get(\"email\", \"N/A\")}')
    print(f'      Ativo: {user.get(\"active\", True)}')
    
    # Testar login
    print('')
    print('   🔐 Testando autenticação...')
    auth_result = auth_manager.authenticate(username, password)
    if auth_result['success']:
        print('      ✅ Senha correta!')
    else:
        print(f'      ❌ Senha incorreta: {auth_result[\"message\"]}')
        print('')
        print('   💡 Recriando usuário com senha correta...')
        # Deletar usuário antigo
        try:
            auth_manager.supabase.table('maestro_users').delete().eq('id', user['id']).execute()
            print('      ✅ Usuário antigo removido')
        except:
            pass
        # Criar novo
        create_result = auth_manager.create_user(username, password, email)
        if create_result['success']:
            print(f'      ✅ Usuário recriado! ID: {create_result.get(\"user_id\")}')
        else:
            print(f'      ❌ Erro: {create_result[\"message\"]}')
else:
    print(f'   ❌ Usuário \"{username}\" não encontrado')
    print('   💡 Criando usuário...')
    create_result = auth_manager.create_user(username, password, email)
    if create_result['success']:
        print(f'   ✅ Usuário criado! ID: {create_result.get(\"user_id\")}')
    else:
        print(f'   ❌ Erro: {create_result[\"message\"]}')
"
echo ""

# 5. Teste final de login
echo "5️⃣ Teste final de autenticação..."
docker exec "$CONTAINER_NAME" python -c "
from auth import auth_manager

username = 'Opera'
password = 'Opera@2026'

result = auth_manager.authenticate(username, password)
if result['success']:
    print('   ✅ LOGIN FUNCIONANDO CORRETAMENTE!')
    print(f'      User ID: {result[\"user\"][\"id\"]}')
    print(f'      Username: {result[\"user\"][\"username\"]}')
else:
    print(f'   ❌ FALHA NO LOGIN: {result[\"message\"]}')
"
echo ""

echo "=================================================="
echo "✅ Diagnóstico concluído!"
echo ""
echo "📝 Credenciais para teste:"
echo "   Usuário: Opera"
echo "   Senha: Opera@2026"
echo ""

