#!/bin/bash

# Script para verificar se há Apache ou proxy bloqueando

echo "🔍 Verificando processos Apache..."
echo ""

# Verificar processos Apache
APACHE_PROCS=$(ps aux | grep -E "httpd|apache2" | grep -v grep)
if [ ! -z "$APACHE_PROCS" ]; then
    echo "⚠️  Processos Apache encontrados:"
    echo "$APACHE_PROCS"
    echo ""
else
    echo "✅ Nenhum processo Apache encontrado"
    echo ""
fi

# Verificar portas
echo "🔍 Verificando portas 80 e 443..."
echo ""
echo "Porta 80:"
sudo lsof -i :80 2>/dev/null | head -10
echo ""
echo "Porta 443:"
sudo lsof -i :443 2>/dev/null | head -10
echo ""

# Verificar DNS local vs remoto
echo "🔍 Verificando DNS..."
echo ""
echo "DNS local (servidor):"
LOCAL_DNS=$(dig +short maestro.opera.security 2>/dev/null | tail -n1)
echo "  $LOCAL_DNS"
echo ""
echo "DNS público (Google 8.8.8.8):"
PUBLIC_DNS=$(dig @8.8.8.8 +short maestro.opera.security 2>/dev/null | tail -n1)
echo "  $PUBLIC_DNS"
echo ""

# Testar acesso direto ao IP
echo "🔍 Testando acesso direto ao IP..."
echo ""
echo "curl -I https://186.227.125.170 --insecure"
curl -I https://186.227.125.170 --insecure 2>&1 | head -5
echo ""

# Testar acesso pelo domínio
echo "🔍 Testando acesso pelo domínio..."
echo ""
echo "curl -I https://maestro.opera.security --insecure"
curl -I https://maestro.opera.security --insecure 2>&1 | head -5
echo ""

# Verificar se há proxy reverso configurado
echo "🔍 Verificando configurações de proxy..."
echo ""
if [ -f /etc/nginx/nginx.conf ]; then
    echo "⚠️  Nginx instalado no sistema (não Docker):"
    systemctl status nginx 2>/dev/null | head -5
    echo ""
fi

if [ -f /etc/httpd/conf/httpd.conf ]; then
    echo "⚠️  Configuração Apache encontrada:"
    echo "  /etc/httpd/conf/httpd.conf"
    echo ""
fi

# Verificar se há firewall/proxy na frente
echo "🔍 Verificando se há proxy reverso na frente..."
echo ""
echo "Testando com Host header:"
curl -I -H "Host: maestro.opera.security" https://186.227.125.170 --insecure 2>&1 | head -5
echo ""

echo "✅ Verificação concluída!"

