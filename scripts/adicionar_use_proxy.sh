#!/bin/bash

# Script para adicionar USE_PROXY ao .env

echo "🔧 Adicionando USE_PROXY ao arquivo .env..."
echo ""

if [ ! -f ".env" ]; then
    echo "❌ Arquivo .env não encontrado!"
    echo "   Execute primeiro: ./criar_env_completo.sh"
    exit 1
fi

# Verificar se USE_PROXY já existe
if grep -q "^USE_PROXY=" .env; then
    echo "✅ USE_PROXY já existe no .env"
    echo ""
    echo "Valor atual:"
    grep "^USE_PROXY=" .env
    echo ""
    read -p "Deseja alterar? (s/N): " alterar
    if [ "$alterar" != "s" ] && [ "$alterar" != "S" ]; then
        echo "❌ Operação cancelada"
        exit 0
    fi
    # Remover linha antiga
    sed -i '/^USE_PROXY=/d' .env
fi

# Adicionar USE_PROXY
echo "" >> .env
echo "# Configuração de Proxy" >> .env
echo "# USE_PROXY=True: Aplicações acessadas através do Maestro (recomendado)" >> .env
echo "# USE_PROXY=False: Aplicações acessadas diretamente (requer portas expostas)" >> .env
echo "USE_PROXY=True" >> .env

# Converter quebras de linha
if command -v dos2unix &> /dev/null; then
    dos2unix .env 2>/dev/null
else
    sed -i 's/\r$//' .env 2>/dev/null
fi

echo "✅ USE_PROXY adicionado ao .env"
echo ""
echo "📋 Conteúdo adicionado:"
echo "   USE_PROXY=True"
echo ""
echo "💡 Para alterar, edite o arquivo .env:"
echo "   nano .env"
echo ""

