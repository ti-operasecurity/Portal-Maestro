#!/bin/bash

# Script para parar Apache que está interceptando requisições

echo "🔍 Verificando se Apache está rodando..."

# Verificar Apache (httpd) - CentOS/RHEL
if systemctl is-active --quiet httpd 2>/dev/null; then
    echo "⚠️  Apache (httpd) está rodando!"
    echo ""
    read -p "Deseja parar o Apache (httpd)? (s/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        echo "🛑 Parando Apache (httpd)..."
        sudo systemctl stop httpd 2>/dev/null || systemctl stop httpd 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "✅ Apache (httpd) parado com sucesso!"
            echo ""
            read -p "Deseja desabilitar o Apache para não iniciar no boot? (s/n): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Ss]$ ]]; then
                sudo systemctl disable httpd 2>/dev/null || systemctl disable httpd 2>/dev/null
                echo "✅ Apache (httpd) desabilitado"
            fi
        else
            echo "❌ Erro ao parar Apache (httpd)"
        fi
    fi
fi

# Verificar Apache (apache2) - Debian/Ubuntu
if systemctl is-active --quiet apache2 2>/dev/null; then
    echo "⚠️  Apache (apache2) está rodando!"
    echo ""
    read -p "Deseja parar o Apache (apache2)? (s/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        echo "🛑 Parando Apache (apache2)..."
        sudo systemctl stop apache2 2>/dev/null || systemctl stop apache2 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "✅ Apache (apache2) parado com sucesso!"
            echo ""
            read -p "Deseja desabilitar o Apache para não iniciar no boot? (s/n): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Ss]$ ]]; then
                sudo systemctl disable apache2 2>/dev/null || systemctl disable apache2 2>/dev/null
                echo "✅ Apache (apache2) desabilitado"
            fi
        else
            echo "❌ Erro ao parar Apache (apache2)"
        fi
    fi
fi

# Verificar processos Apache diretamente
APACHE_PIDS=$(pgrep -f "httpd|apache2" 2>/dev/null)
if [ ! -z "$APACHE_PIDS" ]; then
    echo ""
    echo "⚠️  Processos Apache encontrados:"
    ps aux | grep -E "httpd|apache2" | grep -v grep
    echo ""
    read -p "Deseja matar todos os processos Apache? (s/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        echo "🛑 Matando processos Apache..."
        sudo pkill -9 httpd 2>/dev/null || pkill -9 httpd 2>/dev/null
        sudo pkill -9 apache2 2>/dev/null || pkill -9 apache2 2>/dev/null
        sleep 2
        if [ -z "$(pgrep -f "httpd|apache2" 2>/dev/null)" ]; then
            echo "✅ Processos Apache finalizados!"
        else
            echo "⚠️  Alguns processos ainda estão rodando"
        fi
    fi
fi

# Verificar portas 80 e 443
echo ""
echo "🔍 Verificando portas 80 e 443..."
PORTA_80=$(sudo lsof -i :80 2>/dev/null | grep -v "nginx\|docker" | tail -n +2)
PORTA_443=$(sudo lsof -i :443 2>/dev/null | grep -v "nginx\|docker" | tail -n +2)

if [ ! -z "$PORTA_80" ]; then
    echo "⚠️  Porta 80 está sendo usada por:"
    echo "$PORTA_80"
fi

if [ ! -z "$PORTA_443" ]; then
    echo "⚠️  Porta 443 está sendo usada por:"
    echo "$PORTA_443"
fi

# Verificar se Nginx do Docker está rodando
echo ""
echo "🔍 Verificando Nginx do Docker..."
if docker ps | grep -q "maestro-nginx"; then
    echo "✅ Nginx do Docker está rodando"
else
    echo "❌ Nginx do Docker não está rodando"
    echo "📋 Execute: docker-compose up -d"
fi

echo ""
echo "✅ Verificação concluída!"

