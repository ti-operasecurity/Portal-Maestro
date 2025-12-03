#!/bin/bash

# Script para adicionar usuário via container Docker
# Uso: ./adicionar_usuario.sh

CONTAINER_NAME="maestro-portal"

# Verificar se container está rodando
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo "❌ Container $CONTAINER_NAME não está rodando!"
    echo "   Inicie o container primeiro com: ./deploy-linux.sh --start"
    exit 1
fi

echo "🔐 ADICIONAR NOVO USUÁRIO"
echo "=========================="
echo ""

# Solicitar informações
read -p "Digite o nome de usuário: " username
read -sp "Digite a senha: " password
echo ""
read -sp "Confirme a senha: " password_confirm
echo ""

# Verificar se senhas coincidem
if [ "$password" != "$password_confirm" ]; then
    echo "❌ As senhas não coincidem!"
    exit 1
fi

# Solicitar email (opcional)
read -p "Digite o email (opcional, pressione Enter para pular): " email

echo ""
echo "📋 Resumo:"
echo "   Usuário: $username"
echo "   Email: ${email:-Não informado}"
echo ""

read -p "Confirma a criação deste usuário? (s/N): " confirmar

if [ "$confirmar" != "s" ] && [ "$confirmar" != "S" ]; then
    echo "❌ Operação cancelada"
    exit 0
fi

echo ""
echo "⏳ Criando usuário..."

# Executar no container
docker exec -i "$CONTAINER_NAME" python3 << PYTHON_SCRIPT
import sys
from auth import auth_manager

username = "$username"
password = "$password"
email = "$email" if "$email" else None

try:
    # Verificar se usuário já existe
    result = auth_manager.supabase.table('maestro_users').select('id, username').eq('username', username).execute()
    
    if result.data:
        # Atualizar senha
        user_id = result.data[0]['id']
        hashed_password = auth_manager.hash_password(password)
        auth_manager.supabase.table('maestro_users').update({
            'password_hash': hashed_password
        }).eq('id', user_id).execute()
        print(f"✅ Senha do usuário '{username}' atualizada com sucesso!")
    else:
        # Criar novo usuário
        resultado = auth_manager.create_user(username, password, email)
        if resultado['success']:
            print(f"✅ Usuário '{username}' criado com sucesso!")
            if 'user_id' in resultado:
                print(f"   ID do usuário: {resultado['user_id']}")
        else:
            print(f"❌ Erro: {resultado['message']}")
            sys.exit(1)
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
    echo "❌ Erro ao criar usuário"
    exit 1
fi

