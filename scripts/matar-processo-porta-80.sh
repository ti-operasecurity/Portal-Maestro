#!/bin/bash

# Script para matar processo usando porta 80

echo "🔍 Verificando processos usando porta 80..."

# Tenta múltiplas formas de identificar
PID=""

# Método 1: lsof
if command -v lsof > /dev/null 2>&1; then
    PID=$(lsof -ti :80 2>/dev/null | head -1)
fi

# Método 2: netstat
if [ -z "$PID" ] && command -v netstat > /dev/null 2>&1; then
    PID=$(netstat -tulpn 2>/dev/null | grep :80 | grep LISTEN | awk '{print $7}' | cut -d'/' -f1 | head -1)
fi

# Método 3: ss
if [ -z "$PID" ] && command -v ss > /dev/null 2>&1; then
    PID=$(ss -tulpn 2>/dev/null | grep :80 | grep LISTEN | awk '{print $6}' | cut -d',' -f2 | cut -d'=' -f2 | head -1)
fi

# Método 4: fuser
if [ -z "$PID" ] && command -v fuser > /dev/null 2>&1; then
    PID=$(fuser 80/tcp 2>/dev/null | awk '{print $1}' | head -1)
fi

if [ -z "$PID" ]; then
    echo "❌ Não foi possível identificar processo usando porta 80"
    echo ""
    echo "📋 Tente manualmente:"
    echo "   sudo lsof -i :80"
    echo "   sudo netstat -tulpn | grep :80"
    echo "   sudo ss -tulpn | grep :80"
    exit 1
fi

echo "✅ Processo encontrado: PID $PID"

# Verifica se processo ainda existe
if ! ps -p "$PID" > /dev/null 2>&1; then
    echo "✅ Processo já não existe mais"
    exit 0
fi

# Mostra informações do processo
echo ""
echo "📋 Informações do processo:"
ps -p "$PID" -o pid,ppid,user,cmd 2>/dev/null || ps -p "$PID" -o pid,user,cmd 2>/dev/null

echo ""
read -p "Deseja matar o processo PID $PID? (s/n): " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    echo "❌ Operação cancelada"
    exit 0
fi

# Tenta kill normal primeiro
echo "🛑 Enviando SIGTERM para processo $PID..."
kill "$PID" 2>/dev/null || sudo kill "$PID" 2>/dev/null

# Aguarda 3 segundos
sleep 3

# Verifica se ainda está rodando
if ps -p "$PID" > /dev/null 2>&1; then
    echo "⚠️  Processo ainda rodando, enviando SIGKILL..."
    kill -9 "$PID" 2>/dev/null || sudo kill -9 "$PID" 2>/dev/null
    sleep 1
fi

# Verifica novamente
if ps -p "$PID" > /dev/null 2>&1; then
    echo "❌ Não foi possível matar o processo $PID"
    echo "📋 Tente manualmente:"
    echo "   sudo kill -9 $PID"
    exit 1
else
    echo "✅ Processo $PID foi encerrado com sucesso!"
fi

# Verifica se porta 80 está livre
echo ""
echo "🔍 Verificando porta 80..."
sleep 2

if lsof -i :80 > /dev/null 2>&1 || (command -v netstat > /dev/null 2>&1 && netstat -tulpn 2>/dev/null | grep :80 > /dev/null); then
    echo "⚠️  Porta 80 ainda está em uso!"
    echo "📋 Pode haver outro processo. Execute:"
    echo "   sudo lsof -i :80"
    echo "   sudo netstat -tulpn | grep :80"
else
    echo "✅ Porta 80 está livre!"
    echo ""
    echo "🚀 Agora você pode executar:"
    echo "   ./deploy-linux.sh --start"
fi

