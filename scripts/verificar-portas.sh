#!/bin/bash
# Script para verificar configuração de portas
# Uso: ./verificar-portas.sh

echo "🔍 Verificando configuração de portas..."
echo "========================================"
echo ""

# Verificar firewall
echo "📋 Firewall (firewalld):"
if command -v firewall-cmd &> /dev/null; then
    echo "Portas abertas:"
    sudo firewall-cmd --list-ports 2>/dev/null || echo "  (nenhuma porta customizada)"
    echo ""
    echo "Serviços ativos:"
    sudo firewall-cmd --list-services 2>/dev/null || echo "  (nenhum serviço)"
    echo ""
    
    # Verificar se porta 8000 está aberta
    if sudo firewall-cmd --list-ports 2>/dev/null | grep -q "8000"; then
        echo "⚠️  ATENÇÃO: Porta 8000 está exposta no firewall!"
        echo "   Execute: sudo firewall-cmd --permanent --remove-port=8000/tcp && sudo firewall-cmd --reload"
    else
        echo "✅ Porta 8000 não está exposta no firewall (correto)"
    fi
    
    # Verificar se portas 80 e 443 estão abertas
    if sudo firewall-cmd --list-services 2>/dev/null | grep -q "http"; then
        echo "✅ Porta 80 (HTTP) está aberta"
    else
        echo "⚠️  Porta 80 (HTTP) não está aberta"
    fi
    
    if sudo firewall-cmd --list-services 2>/dev/null | grep -q "https"; then
        echo "✅ Porta 443 (HTTPS) está aberta"
    else
        echo "⚠️  Porta 443 (HTTPS) não está aberta"
    fi
else
    echo "⚠️  firewalld não encontrado"
fi

echo ""
echo "📋 Docker Containers:"
if command -v docker &> /dev/null; then
    echo "Portas expostas pelos containers:"
    docker ps --format "table {{.Names}}\t{{.Ports}}" 2>/dev/null || echo "  Docker não está rodando"
    
    # Verificar docker-compose
    if [ -f "docker-compose.yml" ]; then
        echo ""
        echo "📋 Docker Compose (docker-compose.yml):"
        
        # Verificar se porta 8000 está em 'ports' (errado) ou 'expose' (correto)
        if grep -A 5 "maestro-portal:" docker-compose.yml | grep -q "ports:"; then
            if grep -A 10 "maestro-portal:" docker-compose.yml | grep -q "8000"; then
                echo "⚠️  ATENÇÃO: Porta 8000 está em 'ports' no docker-compose.yml"
                echo "   Deve estar em 'expose' ao invés de 'ports'"
            fi
        else
            if grep -A 5 "maestro-portal:" docker-compose.yml | grep -q "expose:"; then
                echo "✅ Porta 8000 está em 'expose' (correto - apenas interna)"
            fi
        fi
        
        # Verificar Nginx
        if grep -A 10 "nginx:" docker-compose.yml | grep -q "80:80"; then
            echo "✅ Nginx expõe porta 80 (correto)"
        else
            echo "⚠️  Nginx não expõe porta 80"
        fi
        
        if grep -A 10 "nginx:" docker-compose.yml | grep -q "443:443"; then
            echo "✅ Nginx expõe porta 443 (correto)"
        else
            echo "⚠️  Nginx não expõe porta 443"
        fi
    fi
else
    echo "⚠️  Docker não encontrado"
fi

echo ""
echo "📋 Portas em Uso (netstat/ss):"
if command -v ss &> /dev/null; then
    echo "Portas 80, 443, 8000:"
    sudo ss -tulpn | grep -E ':(80|443|8000)\s' || echo "  (nenhuma encontrada)"
elif command -v netstat &> /dev/null; then
    echo "Portas 80, 443, 8000:"
    sudo netstat -tulpn | grep -E ':(80|443|8000)\s' || echo "  (nenhuma encontrada)"
else
    echo "⚠️  netstat/ss não encontrado"
fi

echo ""
echo "🧪 Testes de Conectividade:"
echo ""

# Testar porta 8000 localmente
if curl -s --connect-timeout 2 http://localhost:8000 > /dev/null 2>&1; then
    echo "✅ Porta 8000 acessível localmente (correto - apenas interno)"
else
    echo "ℹ️  Porta 8000 não acessível localmente (pode estar parado)"
fi

# Testar porta 80
if curl -s --connect-timeout 2 http://localhost:80 > /dev/null 2>&1; then
    echo "✅ Porta 80 acessível localmente"
else
    echo "⚠️  Porta 80 não acessível localmente"
fi

# Testar porta 443
if curl -s --connect-timeout 2 -k https://localhost:443 > /dev/null 2>&1; then
    echo "✅ Porta 443 acessível localmente"
else
    echo "⚠️  Porta 443 não acessível localmente"
fi

echo ""
echo "========================================"
echo "✅ Verificação concluída!"
echo ""
echo "📚 Para mais informações, consulte:"
echo "   docs/CONFIGURACAO_PORTAS.md"

