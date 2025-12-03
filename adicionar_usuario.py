#!/usr/bin/env python3
"""
Script para adicionar novos usuários ao banco de dados
Uso: python adicionar_usuario.py
"""

import os
import sys
from getpass import getpass
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

try:
    from auth import auth_manager
except ImportError:
    print("❌ Erro: Não foi possível importar auth_manager")
    print("   Certifique-se de que está executando na raiz do projeto")
    sys.exit(1)

def validar_username(username):
    """Valida o nome de usuário"""
    if not username or len(username.strip()) < 3:
        return False, "Nome de usuário deve ter pelo menos 3 caracteres"
    if len(username) > 50:
        return False, "Nome de usuário deve ter no máximo 50 caracteres"
    # Permite letras, números, ponto (.), underscore (_) e hífen (-)
    if not username.replace('_', '').replace('-', '').replace('.', '').isalnum():
        return False, "Nome de usuário deve conter apenas letras, números, ponto (.), underscore (_) e hífen (-)"
    return True, None

def validar_senha(senha):
    """Valida a senha"""
    if not senha or len(senha) < 6:
        return False, "Senha deve ter pelo menos 6 caracteres"
    if len(senha) > 100:
        return False, "Senha muito longa (máximo 100 caracteres)"
    return True, None

def adicionar_usuario():
    """Função principal para adicionar usuário"""
    print("=" * 60)
    print("🔐 ADICIONAR NOVO USUÁRIO")
    print("=" * 60)
    print()
    
    # Solicitar username
    while True:
        username = input("Digite o nome de usuário: ").strip()
        valido, mensagem = validar_username(username)
        if valido:
            break
        print(f"❌ {mensagem}")
        print()
    
    # Verificar se usuário já existe
    try:
        result = auth_manager.supabase.table('maestro_users').select('id, username').eq('username', username).execute()
        if result.data:
            print(f"⚠️  Usuário '{username}' já existe!")
            resposta = input("Deseja alterar a senha deste usuário? (s/N): ").strip().lower()
            if resposta != 's':
                print("❌ Operação cancelada")
                return
            # Continuar para alterar senha
        else:
            print(f"✅ Usuário '{username}' não existe. Criando novo usuário...")
    except Exception as e:
        print(f"❌ Erro ao verificar usuário: {str(e)}")
        return
    
    # Solicitar senha
    while True:
        senha = getpass("Digite a senha: ")
        valido, mensagem = validar_senha(senha)
        if valido:
            break
        print(f"❌ {mensagem}")
        print()
    
    # Confirmar senha
    senha_confirmacao = getpass("Confirme a senha: ")
    if senha != senha_confirmacao:
        print("❌ As senhas não coincidem!")
        return
    
    # Solicitar email (opcional)
    email = input("Digite o email (opcional, pressione Enter para pular): ").strip()
    if email and '@' not in email:
        print("⚠️  Email inválido. Continuando sem email...")
        email = None
    
    print()
    print("📋 Resumo:")
    print(f"   Usuário: {username}")
    print(f"   Email: {email or 'Não informado'}")
    print()
    
    confirmar = input("Confirma a criação deste usuário? (s/N): ").strip().lower()
    if confirmar != 's':
        print("❌ Operação cancelada")
        return
    
    print()
    print("⏳ Criando usuário...")
    
    try:
        # Se usuário já existe, atualizar senha
        if result.data:
            user_id = result.data[0]['id']
            hashed_password = auth_manager.hash_password(senha)
            auth_manager.supabase.table('maestro_users').update({
                'password_hash': hashed_password
            }).eq('id', user_id).execute()
            print(f"✅ Senha do usuário '{username}' atualizada com sucesso!")
        else:
            # Criar novo usuário
            resultado = auth_manager.create_user(username, senha, email)
            if resultado['success']:
                print(f"✅ Usuário '{username}' criado com sucesso!")
                if 'user_id' in resultado:
                    print(f"   ID do usuário: {resultado['user_id']}")
            else:
                print(f"❌ Erro ao criar usuário: {resultado['message']}")
                return
        
        print()
        print("=" * 60)
        print("✅ Operação concluída com sucesso!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Erro ao criar/atualizar usuário: {str(e)}")
        import traceback
        traceback.print_exc()
        return

if __name__ == '__main__':
    try:
        adicionar_usuario()
    except KeyboardInterrupt:
        print("\n\n❌ Operação cancelada pelo usuário")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erro inesperado: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
