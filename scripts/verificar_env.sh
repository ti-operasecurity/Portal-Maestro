#!/bin/bash

# Script para verificar se o arquivo .env está correto

echo "🔍 Verificando arquivo .env..."
echo ""

if [ ! -f ".env" ]; then
    echo "❌ Arquivo .env não encontrado!"
    exit 1
fi

echo "✅ Arquivo .env encontrado"
echo ""
echo "📋 Conteúdo (valores mascarados):"
echo "-----------------------------------"

# Verifica cada variável essencial
vars_ok=0
vars_missing=0

check_var() {
    local var_name=$1
    if grep -q "^[[:space:]]*${var_name}[[:space:]]*=" .env; then
        local value=$(grep "^[[:space:]]*${var_name}[[:space:]]*=" .env | cut -d '=' -f 2- | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | tr -d '\r\n')
        if [ -n "$value" ]; then
            local preview="${value:0:30}..."
            echo "  ✅ ${var_name}=${preview}"
            ((vars_ok++))
        else
            echo "  ⚠️  ${var_name}= (vazio)"
            ((vars_missing++))
        fi
    else
        echo "  ❌ ${var_name} (não encontrada)"
        ((vars_missing++))
    fi
}

check_var "SUPABASE_URL"
check_var "SUPABASE_SERVICE_ROLE_KEY"
check_var "SECRET_KEY"
check_var "SESSION_COOKIE_SECURE"
check_var "SESSION_COOKIE_HTTPONLY"
check_var "SESSION_COOKIE_SAMESITE"

echo "-----------------------------------"
echo ""

# Verificar problemas comuns
echo "🔧 Verificando problemas comuns..."
echo ""

# Verificar espaços ao redor do =
if grep -q "[[:space:]]*=[[:space:]]" .env; then
    echo "  ⚠️  Encontrado espaços ao redor do '=' (não recomendado, mas aceito)"
fi

# Verificar caracteres \r
if grep -q $'\r' .env; then
    echo "  ⚠️  Encontrado caracteres \\r (carriage return do Windows)"
    echo "      Execute: dos2unix .env ou sed -i 's/\\r$//' .env"
fi

# Verificar linhas vazias ou comentários (ok)
echo "  ✅ Linhas vazias e comentários são aceitos"

echo ""
echo "📊 Resumo:"
echo "  Variáveis encontradas: ${vars_ok}"
echo "  Variáveis faltando/vazias: ${vars_missing}"
echo ""

if [ $vars_missing -eq 0 ]; then
    echo "✅ Arquivo .env parece estar correto!"
    echo ""
    echo "💡 Teste carregar as variáveis:"
    echo "   source <(grep -v '^#' .env | sed 's/^/export /')"
    echo "   echo \$SUPABASE_URL"
else
    echo "❌ Algumas variáveis estão faltando ou vazias!"
    echo "   Corrija o arquivo .env antes de continuar"
fi

