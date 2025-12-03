#!/bin/bash

# Script para verificar se requisições estão chegando ao Nginx

echo "🔍 Verificando requisições recentes no Nginx..."
echo ""

# Ver logs de acesso dos últimos 2 minutos
echo "📋 Requisições dos últimos 2 minutos:"
docker exec maestro-nginx tail -50 /var/log/nginx/maestro_access.log 2>/dev/null | tail -20 || echo "Log não encontrado"
echo ""

# Ver logs de erro
echo "📋 Erros recentes:"
docker exec maestro-nginx tail -20 /var/log/nginx/maestro_error.log 2>/dev/null || echo "Nenhum erro encontrado"
echo ""

# Ver logs do container
echo "📋 Últimas requisições no container:"
docker-compose logs nginx --tail=30 | grep -E "(GET|POST|HEAD|403|404|500)" || docker-compose logs nginx --tail=10
echo ""

# Verificar se há requisições com 403
echo "🔍 Verificando se há requisições 403:"
docker exec maestro-nginx grep "403" /var/log/nginx/maestro_access.log 2>/dev/null | tail -5 || echo "Nenhuma requisição 403 encontrada nos logs do Nginx"
echo ""

echo "✅ Verificação concluída!"
echo ""
echo "💡 Se você não vê suas requisições aqui quando acessa pelo navegador,"
echo "   significa que elas não estão chegando ao Nginx (provavelmente"
echo "   interceptadas pelo Fortinet ou outro proxy)."

