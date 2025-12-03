#!/bin/bash

# Script para limpar containers antigos e fazer redeploy

echo "🧹 Limpando containers e imagens antigas..."
echo ""

# Parar e remover container se existir
if docker ps -a | grep -q maestro-portal; then
    echo "🛑 Parando container existente..."
    docker stop maestro-portal 2>/dev/null || true
    docker rm maestro-portal 2>/dev/null || true
    echo "✅ Container removido"
fi

# Remover containers órfãos do docker-compose
echo ""
echo "🧹 Limpando containers do docker-compose..."
docker-compose down 2>/dev/null || true

# Remover imagens antigas (opcional - descomente se quiser)
# echo ""
# echo "🗑️  Removendo imagens antigas..."
# docker rmi maestro-maestro-portal 2>/dev/null || true
# docker rmi maestro-portal:v1.0 2>/dev/null || true

echo ""
echo "✅ Limpeza concluída!"
echo ""
echo "🚀 Agora você pode fazer o deploy:"
echo "   docker-compose up -d --build"
echo "   # ou"
echo "   ./deploy-linux.sh --full-deploy"
echo ""

