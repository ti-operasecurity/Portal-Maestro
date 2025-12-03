"""
Script de configuração inicial do sistema Maestro
Execute: python setup.py
"""
import os
import secrets
from dotenv import load_dotenv

def generate_secret_key():
    """Gera uma chave secreta aleatória"""
    return secrets.token_hex(32)

def setup_env():
    """Configura o arquivo .env"""
    env_file = '.env'
    
    if os.path.exists(env_file):
        print("⚠️  Arquivo .env já existe!")
        response = input("Deseja sobrescrever? (s/N): ").strip().lower()
        if response != 's':
            print("Operação cancelada.")
            return
    
    print("\n🔧 Configuração do Sistema Maestro")
    print("=" * 50)
    
    # Supabase
    print("\n📊 Configuração do Supabase:")
    supabase_url = input("SUPABASE_URL (ex: https://xxxxx.supabase.co): ").strip()
    supabase_service_role_key = input("SUPABASE_SERVICE_ROLE_KEY (service_role key): ").strip()
    
    # Secret Key
    print("\n🔐 Gerando SECRET_KEY...")
    secret_key = generate_secret_key()
    print(f"✅ SECRET_KEY gerada: {secret_key[:20]}...")
    
    # Configurações de sessão
    print("\n🍪 Configurações de Sessão:")
    cookie_secure = input("SESSION_COOKIE_SECURE (True/False) [True]: ").strip() or "True"
    cookie_httponly = input("SESSION_COOKIE_HTTPONLY (True/False) [True]: ").strip() or "True"
    cookie_samesite = input("SESSION_COOKIE_SAMESITE (Lax/Strict/None) [Lax]: ").strip() or "Lax"
    
    # Cria arquivo .env
    env_content = f"""# Supabase Configuration
SUPABASE_URL={supabase_url}
SUPABASE_SERVICE_ROLE_KEY={supabase_service_role_key}

# Flask Security
SECRET_KEY={secret_key}
SESSION_COOKIE_SECURE={cookie_secure}
SESSION_COOKIE_HTTPONLY={cookie_httponly}
SESSION_COOKIE_SAMESITE={cookie_samesite}

# Database (PostgreSQL - se necessário)
DB_HOST=
DB_USER=
DB_PSW=
DB_PORT=5432
DB_NAME=
"""
    
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print(f"\n✅ Arquivo .env criado com sucesso!")
    print("\n📝 Próximos passos:")
    print("1. Execute o script SQL no Supabase (supabase_setup.sql)")
    print("2. Execute: python create_test_user.py")
    print("3. Execute: python app.py")

if __name__ == '__main__':
    try:
        setup_env()
    except KeyboardInterrupt:
        print("\n\nOperação cancelada pelo usuário.")
    except Exception as e:
        print(f"\n❌ Erro: {str(e)}")

