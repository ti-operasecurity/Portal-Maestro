#!/bin/bash

# Script para build usando --network=host (bypassa algumas restrições do Fortinet)

set -e

echo "🔧 Build com --network=host (bypassa restrições do Fortinet)"
echo ""

# Para containers existentes
echo "🛑 Parando containers..."
docker-compose down 2>/dev/null || true

# Build com network host
echo "📦 Construindo imagem com --network=host..."
docker build --network=host -t maestro-maestro-portal:latest .

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Build concluído com sucesso!"
    echo ""
    echo "🚀 Iniciando containers..."
    docker-compose up -d
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Containers iniciados!"
        echo ""
        echo "📋 Verificar status:"
        echo "   docker ps"
        echo "   docker-compose logs -f"
    else
        echo "❌ Erro ao iniciar containers"
        exit 1
    fi
else
    echo ""
    echo "❌ Build falhou"
    exit 1
fi

