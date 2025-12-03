#!/bin/bash

# Script para criar/atualizar arquivo .env completo

echo "🔧 Criando arquivo .env completo..."
echo ""

# Verificar se .env existe e ler valores existentes
if [ -f ".env" ]; then
    echo "📋 Arquivo .env encontrado. Lendo valores existentes..."
    
    # Ler valores existentes (removendo \r)
    EXISTING_SUPABASE_URL=$(grep "^SUPABASE_URL=" .env 2>/dev/null | cut -d '=' -f 2- | tr -d '\r\n' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | sed -e "s/^['\"]//" -e "s/['\"]$//")
    EXISTING_SUPABASE_KEY=$(grep "^SUPABASE_SERVICE_ROLE_KEY=" .env 2>/dev/null | cut -d '=' -f 2- | tr -d '\r\n' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | sed -e "s/^['\"]//" -e "s/['\"]$//")
    EXISTING_SECRET_KEY=$(grep "^SECRET_KEY=" .env 2>/dev/null | cut -d '=' -f 2- | tr -d '\r\n' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | sed -e "s/^['\"]//" -e "s/['\"]$//")
    
    if [ -n "$EXISTING_SUPABASE_URL" ] && [ "$EXISTING_SUPABASE_URL" != "https://seu-projeto.supabase.co" ]; then
        echo "   ✅ SUPABASE_URL preservado: ${EXISTING_SUPABASE_URL:0:30}..."
    else
        echo "   ⚠️  SUPABASE_URL não encontrado ou é placeholder"
        EXISTING_SUPABASE_URL=""
    fi
    
    if [ -n "$EXISTING_SUPABASE_KEY" ] && [ "$EXISTING_SUPABASE_KEY" != "sua_chave_service_role_aqui" ]; then
        echo "   ✅ SUPABASE_SERVICE_ROLE_KEY preservado: ${EXISTING_SUPABASE_KEY:0:30}..."
    else
        echo "   ⚠️  SUPABASE_SERVICE_ROLE_KEY não encontrado ou é placeholder"
        EXISTING_SUPABASE_KEY=""
    fi
    
    if [ -n "$EXISTING_SECRET_KEY" ] && [ "$EXISTING_SECRET_KEY" != "sua_chave_secreta_aqui" ]; then
        echo "   ✅ SECRET_KEY preservado"
    else
        echo "   ⚠️  SECRET_KEY não encontrado ou é placeholder"
        EXISTING_SECRET_KEY=""
    fi
else
    echo "📝 Criando novo arquivo .env..."
    EXISTING_SUPABASE_URL=""
    EXISTING_SUPABASE_KEY=""
    EXISTING_SECRET_KEY=""
fi

# Gerar SECRET_KEY se não existir
if [ -z "$EXISTING_SECRET_KEY" ]; then
    echo "🔑 Gerando nova SECRET_KEY..."
    if command -v openssl &> /dev/null; then
        EXISTING_SECRET_KEY=$(openssl rand -hex 32)
    elif command -v python3 &> /dev/null; then
        EXISTING_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    else
        EXISTING_SECRET_KEY=$(date +%s | sha256sum | base64 | head -c 64)
    fi
    echo "   ✅ SECRET_KEY gerada"
fi

# Criar backup
if [ -f ".env" ]; then
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    echo "   💾 Backup criado: .env.backup.*"
fi

# Criar arquivo .env completo
cat > .env << EOF
# Configurações do Supabase
# ⚠️  PREENCHA OS VALORES ABAIXO COM SUAS CREDENCIAIS DO SUPABASE
SUPABASE_URL=${EXISTING_SUPABASE_URL:-https://seu-projeto.supabase.co}
SUPABASE_SERVICE_ROLE_KEY=${EXISTING_SUPABASE_KEY:-sua_chave_service_role_aqui}

# Chave secreta do Flask (OBRIGATÓRIA)
# ✅ Gerada automaticamente - não precisa alterar
SECRET_KEY=${EXISTING_SECRET_KEY}

# Configurações de Sessão
# SESSION_COOKIE_SECURE=False (use True apenas com HTTPS)
SESSION_COOKIE_SECURE=False
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax

# Configurações do Docker (opcional)
HOST_PORT=8000
DEBUG=False
FLASK_ENV=production

# Configuração de Proxy
# USE_PROXY=True: Aplicações acessadas através do Maestro (recomendado)
# USE_PROXY=False: Aplicações acessadas diretamente (requer portas expostas)
USE_PROXY=True
EOF

# Converter quebras de linha
if command -v dos2unix &> /dev/null; then
    dos2unix .env 2>/dev/null
    echo "   ✅ Convertido para formato Unix"
else
    sed -i 's/\r$//' .env 2>/dev/null
    echo "   ✅ Removidos caracteres \\r"
fi

echo ""
echo "✅ Arquivo .env criado/atualizado com sucesso!"
echo ""

# Verificar se precisa preencher valores
if [ -z "$EXISTING_SUPABASE_URL" ] || [ -z "$EXISTING_SUPABASE_KEY" ]; then
    echo "⚠️  ATENÇÃO: Você precisa preencher as credenciais do Supabase!"
    echo ""
    echo "📋 Próximos passos:"
    echo "   1. Edite o arquivo .env:"
    echo "      nano .env"
    echo ""
    echo "   2. Preencha os valores:"
    echo "      - SUPABASE_URL=https://seu-projeto.supabase.co"
    echo "      - SUPABASE_SERVICE_ROLE_KEY=sua_chave_aqui"
    echo ""
    echo "   3. Salve e saia (Ctrl+O, Enter, Ctrl+X)"
    echo ""
    echo "   4. Verifique se está correto:"
    echo "      ./verificar_env.sh"
    echo ""
    echo "   5. Faça o deploy:"
    echo "      ./deploy-compose.sh"
    echo ""
else
    echo "✅ Todas as variáveis estão configuradas!"
    echo ""
    echo "📋 Próximos passos:"
    echo "   1. Verifique se está correto:"
    echo "      ./verificar_env.sh"
    echo ""
    echo "   2. Faça o deploy:"
    echo "      ./deploy-compose.sh"
    echo "      # ou"
    echo "      ./deploy-linux.sh --full-deploy"
    echo ""
fi

