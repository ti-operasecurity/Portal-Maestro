#!/bin/bash

# Script para limpar cache DNS local do servidor

echo "🔍 Limpando cache DNS local..."

# Limpar cache systemd-resolved (Ubuntu/Debian moderno)
if systemctl is-active --quiet systemd-resolved 2>/dev/null; then
    echo "📋 Limpando cache systemd-resolved..."
    sudo systemd-resolve --flush-caches 2>/dev/null || true
    echo "✅ Cache systemd-resolved limpo"
fi

# Limpar cache resolvectl (systemd mais recente)
if command -v resolvectl &> /dev/null; then
    echo "📋 Limpando cache resolvectl..."
    sudo resolvectl flush-caches 2>/dev/null || true
    echo "✅ Cache resolvectl limpo"
fi

# Limpar cache nscd (Name Service Cache Daemon)
if systemctl is-active --quiet nscd 2>/dev/null; then
    echo "📋 Limpando cache nscd..."
    sudo systemctl restart nscd 2>/dev/null || true
    echo "✅ Cache nscd limpo"
fi

# Limpar cache dnsmasq
if systemctl is-active --quiet dnsmasq 2>/dev/null; then
    echo "📋 Limpando cache dnsmasq..."
    sudo systemctl restart dnsmasq 2>/dev/null || true
    echo "✅ Cache dnsmasq limpo"
fi

# Adicionar entrada no /etc/hosts para forçar resolução local
echo ""
echo "🔧 Adicionando entrada no /etc/hosts para forçar resolução correta..."
if ! grep -q "maestro.opera.security" /etc/hosts; then
    echo "186.227.125.170 maestro.opera.security" | sudo tee -a /etc/hosts > /dev/null
    echo "✅ Entrada adicionada ao /etc/hosts"
else
    echo "⚠️  Entrada já existe no /etc/hosts"
    # Atualizar se estiver com IP errado
    sudo sed -i 's/.*maestro\.opera\.security/186.227.125.170 maestro.opera.security/' /etc/hosts
    echo "✅ Entrada atualizada no /etc/hosts"
fi

echo ""
echo "🔍 Verificando DNS após limpeza..."
echo ""
echo "DNS local (servidor):"
dig +short maestro.opera.security 2>/dev/null | tail -n1
echo ""
echo "DNS público (Google 8.8.8.8):"
dig @8.8.8.8 +short maestro.opera.security 2>/dev/null | tail -n1
echo ""
echo "Resolução via /etc/hosts:"
getent hosts maestro.opera.security 2>/dev/null || echo "Não encontrado"
echo ""

echo "✅ Cache DNS limpo!"
echo ""
echo "📋 Teste agora:"
echo "   curl -I https://maestro.opera.security --insecure"
echo "   # Deve retornar: server: nginx/1.29.3"

