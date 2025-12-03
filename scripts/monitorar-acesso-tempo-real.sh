#!/bin/bash

# Script para monitorar acessos em tempo real e verificar se chegam ao Nginx

echo "🔍 Monitorando acessos em tempo real..."
echo ""
echo "📋 Quando você acessar https://maestro.opera.security no navegador,"
echo "   as requisições devem aparecer aqui."
echo ""
echo "⏹️  Pressione Ctrl+C para parar"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Monitorar logs do Nginx em tempo real
docker-compose logs -f nginx 2>&1 | grep --line-buffered -E "(GET|POST|HEAD|maestro.opera.security|403|404|500)" || docker-compose logs -f nginx

