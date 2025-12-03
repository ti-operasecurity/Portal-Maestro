"""
Script para criar usuário de teste no Supabase
Execute: python create_test_user.py
"""
import os
from dotenv import load_dotenv
from auth import auth_manager

load_dotenv()

def create_test_user():
    """Cria o usuário de teste"""
    username = "Opera"
    password = "Opera@2026"
    email = "ti@opera.security"
    
    print(f"Criando usuário de teste...")
    print(f"Usuário: {username}")
    print(f"Senha: {password}")
    print("-" * 50)
    
    result = auth_manager.create_user(username, password, email)
    
    if result['success']:
        print("✅ Usuário criado com sucesso!")
        print(f"ID do usuário: {result.get('user_id')}")
    else:
        print(f"❌ Erro ao criar usuário: {result['message']}")
        if 'já existe' in result['message'].lower():
            print("\n💡 O usuário já existe. Você pode fazer login normalmente.")
            print("   Para resetar a senha, delete o usuário no Supabase e execute novamente.")

if __name__ == '__main__':
    try:
        create_test_user()
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        print("\nVerifique se:")
        print("1. O arquivo .env está configurado corretamente")
        print("2. As variáveis SUPABASE_URL e SUPABASE_KEY estão definidas")
        print("3. A tabela 'users' foi criada no Supabase (execute supabase_setup.sql)")

