#!/bin/bash

# Script para identificar e parar serviço usando porta 80

echo "🔍 Verificando o que está usando a porta 80..."

# Verifica se há processo usando porta 80
PROCESSO=$(lsof -i :80 2>/dev/null | tail -n +2 | awk '{print $1, $2}' | head -1)

if [ -z "$PROCESSO" ]; then
    # Tenta com netstat
    PROCESSO=$(netstat -tulpn 2>/dev/null | grep :80 | awk '{print $7}' | head -1)
fi

if [ -z "$PROCESSO" ]; then
    # Tenta com ss
    PROCESSO=$(ss -tulpn 2>/dev/null | grep :80 | awk '{print $6}' | head -1)
fi

if [ -z "$PROCESSO" ]; then
    echo "❌ Não foi possível identificar o processo usando porta 80"
    echo "📋 Tente manualmente:"
    echo "   sudo lsof -i :80"
    echo "   sudo netstat -tulpn | grep :80"
    echo "   sudo ss -tulpn | grep :80"
    exit 1
fi

echo "✅ Processo encontrado: $PROCESSO"

# Extrai PID e nome
PID=$(echo $PROCESSO | awk '{print $2}')
NOME=$(echo $PROCESSO | awk '{print $1}')

if [ -z "$PID" ]; then
    PID=$(echo $PROCESSO | cut -d',' -f2 | cut -d'=' -f2)
fi

echo "📋 Detalhes:"
echo "   Nome: $NOME"
echo "   PID: $PID"

# Verifica se é um serviço systemd
SERVICO=$(systemctl list-units --type=service --state=running 2>/dev/null | grep -i "$NOME" | awk '{print $1}' | head -1)

if [ ! -z "$SERVICO" ]; then
    echo ""
    echo "🔧 Serviço systemd encontrado: $SERVICO"
    echo ""
    read -p "Deseja parar o serviço $SERVICO? (s/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        echo "🛑 Parando serviço $SERVICO..."
        sudo systemctl stop "$SERVICO" 2>/dev/null || systemctl stop "$SERVICO" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "✅ Serviço parado com sucesso!"
            echo ""
            read -p "Deseja desabilitar o serviço para não iniciar no boot? (s/n): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Ss]$ ]]; then
                sudo systemctl disable "$SERVICO" 2>/dev/null || systemctl disable "$SERVICO" 2>/dev/null
                echo "✅ Serviço desabilitado"
            fi
        else
            echo "❌ Erro ao parar serviço"
        fi
    fi
else
    # Tenta parar pelo PID
    if [ ! -z "$PID" ] && [ "$PID" != "PID" ]; then
        echo ""
        read -p "Deseja parar o processo PID $PID ($NOME)? (s/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Ss]$ ]]; then
            echo "🛑 Parando processo $PID..."
            sudo kill "$PID" 2>/dev/null || kill "$PID" 2>/dev/null
            sleep 2
            if ! ps -p "$PID" > /dev/null 2>&1; then
                echo "✅ Processo parado com sucesso!"
            else
                echo "⚠️  Processo ainda rodando, tentando kill -9..."
                sudo kill -9 "$PID" 2>/dev/null || kill -9 "$PID" 2>/dev/null
                sleep 1
                if ! ps -p "$PID" > /dev/null 2>&1; then
                    echo "✅ Processo parado com sucesso!"
                else
                    echo "❌ Não foi possível parar o processo"
                fi
            fi
        fi
    fi
fi

echo ""
echo "🔍 Verificando novamente porta 80..."
sleep 2
if lsof -i :80 > /dev/null 2>&1 || netstat -tulpn 2>/dev/null | grep :80 > /dev/null; then
    echo "⚠️  Porta 80 ainda está em uso!"
    echo "📋 Execute manualmente:"
    echo "   sudo lsof -i :80"
    echo "   sudo kill <PID>"
else
    echo "✅ Porta 80 está livre!"
    echo ""
    echo "🚀 Agora você pode executar:"
    echo "   ./deploy-linux.sh --start"
fi

