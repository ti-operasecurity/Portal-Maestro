#!/usr/bin/env python3
"""
Script para testar conexão com Supabase
Uso: python testar_supabase.py
"""

import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

print("🔍 Testando configuração do Supabase...")
print("=" * 60)
print()

# Verificar variáveis
supabase_url = os.getenv('SUPABASE_URL', '').strip().replace('\r', '').replace('\n', '')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '').strip().replace('\r', '').replace('\n', '')

print("📋 Variáveis de Ambiente:")
print(f"   SUPABASE_URL: {'✅ definida' if supabase_url else '❌ não definida'}")
if supabase_url:
    print(f"      Valor: {supabase_url[:50]}...")
    print(f"      Tamanho: {len(supabase_url)} caracteres")
    if '\r' in supabase_url or '\n' in supabase_url:
        print(f"      ⚠️  CONTÉM caracteres \\r ou \\n!")

print()
print(f"   SUPABASE_SERVICE_ROLE_KEY: {'✅ definida' if supabase_key else '❌ não definida'}")
if supabase_key:
    print(f"      Valor: {supabase_key[:30]}...")
    print(f"      Tamanho: {len(supabase_key)} caracteres")
    if '\r' in supabase_key or '\n' in supabase_key:
        print(f"      ⚠️  CONTÉM caracteres \\r ou \\n!")
    # Verificar se começa com eyJ (JWT token)
    if not supabase_key.startswith('eyJ'):
        print(f"      ⚠️  AVISO: A chave não parece ser um JWT válido (deve começar com 'eyJ')")

print()
print("=" * 60)
print()

if not supabase_url or not supabase_key:
    print("❌ Variáveis não configuradas!")
    print()
    print("💡 Solução:")
    print("   1. Verifique se o arquivo .env existe na raiz do projeto")
    print("   2. Verifique se as variáveis estão escritas corretamente:")
    print("      SUPABASE_URL=https://seu-projeto.supabase.co")
    print("      SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    print("   3. Execute: dos2unix .env (para remover caracteres \\r)")
    exit(1)

# Tentar conectar
print("🔌 Testando conexão com Supabase...")
print()

try:
    from supabase import create_client, Client
    
    supabase: Client = create_client(supabase_url, supabase_key)
    
    # Tentar fazer uma query simples
    print("   Testando query simples...")
    result = supabase.table('maestro_users').select('count').limit(1).execute()
    
    print("   ✅ Conexão com Supabase OK!")
    print()
    print("📊 Testando operações:")
    
    # Testar select
    print("   - SELECT: ✅ OK")
    
    # Verificar se a tabela existe e tem estrutura correta
    try:
        test_result = supabase.table('maestro_users').select('id, username').limit(1).execute()
        print("   - Estrutura da tabela: ✅ OK")
    except Exception as e:
        print(f"   - Estrutura da tabela: ❌ Erro - {str(e)}")
    
    print()
    print("=" * 60)
    print("✅ Tudo funcionando corretamente!")
    print("=" * 60)
    
except Exception as e:
    print(f"   ❌ Erro na conexão: {str(e)}")
    print()
    print("💡 Possíveis causas:")
    print("   1. SUPABASE_URL incorreta")
    print("   2. SUPABASE_SERVICE_ROLE_KEY incorreta ou expirada")
    print("   3. Caracteres \\r ou \\n nas variáveis")
    print("   4. Projeto Supabase não existe ou foi deletado")
    print()
    print("🔧 Solução:")
    print("   1. Verifique as credenciais no painel do Supabase")
    print("   2. Copie novamente a SERVICE_ROLE_KEY (não a anon key)")
    print("   3. Execute: dos2unix .env")
    print("   4. Execute este script novamente")
    exit(1)

