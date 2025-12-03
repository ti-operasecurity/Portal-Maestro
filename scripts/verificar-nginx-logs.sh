#!/bin/bash

# Script para verificar logs do Nginx e diagnosticar problema 403

echo "🔍 Verificando logs do Nginx..."
echo ""

# Ver logs de acesso
echo "📋 Últimas 20 linhas do log de acesso:"
docker exec maestro-nginx tail -20 /var/log/nginx/maestro_access.log 2>/dev/null || echo "Log não encontrado"
echo ""

# Ver logs de erro
echo "📋 Últimas 20 linhas do log de erro:"
docker exec maestro-nginx tail -20 /var/log/nginx/maestro_error.log 2>/dev/null || echo "Log não encontrado"
echo ""

# Ver logs gerais do Nginx
echo "📋 Últimas 20 linhas dos logs do container:"
docker-compose logs nginx | tail -20
echo ""

# Verificar configuração ativa
echo "📋 Configuração Nginx ativa:"
docker exec maestro-nginx cat /etc/nginx/conf.d/default.conf | head -30
echo ""

# Testar acesso
echo "🔍 Testando acesso..."
echo ""
echo "1. Teste HTTP (deve redirecionar):"
curl -I http://maestro.opera.security 2>&1 | head -5
echo ""

echo "2. Teste HTTPS:"
curl -I https://maestro.opera.security --insecure 2>&1 | head -5
echo ""

echo "3. Teste com Host header:"
curl -I -H "Host: maestro.opera.security" https://186.227.125.170 --insecure 2>&1 | head -5
echo ""

echo "✅ Verificação concluída!"

