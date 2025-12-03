#!/bin/bash
# Script para limpar containers e imagens Docker
# Uso: ./scripts/limpar-containers.sh

set -e

echo "🧹 Limpando containers e imagens Docker..."

# Parar e remover containers
echo "🛑 Parando containers..."
docker-compose down 2>/dev/null || true

# Remover containers órfãos
echo "🗑️  Removendo containers órfãos..."
docker ps -a | grep maestro | awk '{print $1}' | xargs -r docker rm -f 2>/dev/null || true

# Remover imagens antigas
echo "🗑️  Removendo imagens antigas..."
docker images | grep maestro-portal | awk '{print $3}' | xargs -r docker rmi -f 2>/dev/null || true

# Limpar volumes não utilizados (opcional)
echo "🧹 Limpando volumes não utilizados..."
docker volume prune -f 2>/dev/null || true

echo "✅ Limpeza concluída!"
echo ""
echo "Agora você pode executar:"
echo "  ./deploy-linux.sh --full-deploy"

