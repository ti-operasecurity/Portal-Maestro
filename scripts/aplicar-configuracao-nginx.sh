#!/bin/bash

# Script para aplicar nova configuração do Nginx

echo "🔄 Aplicando nova configuração do Nginx..."
echo ""

# Parar containers
echo "📋 Parando containers..."
docker-compose down

# Iniciar containers (vai copiar nova configuração)
echo "📋 Iniciando containers com nova configuração..."
docker-compose up -d

# Aguardar Nginx iniciar
echo "⏳ Aguardando Nginx iniciar..."
sleep 5

# Verificar se está rodando
echo "🔍 Verificando status..."
docker ps | grep maestro-nginx

# Verificar configuração ativa
echo ""
echo "📋 Configuração ativa (deve ter default_server):"
docker exec maestro-nginx cat /etc/nginx/conf.d/default.conf | grep -A 2 "listen 443"

# Testar configuração
echo ""
echo "🧪 Testando configuração..."
docker exec maestro-nginx nginx -t

echo ""
echo "✅ Configuração aplicada!"
echo ""
echo "📋 Teste agora:"
echo "   curl -I https://maestro.opera.security --insecure"

