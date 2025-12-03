#!/bin/bash

# Script de deploy usando Docker Compose (mais confiável para variáveis de ambiente)

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

log() {
    echo -e "${CYAN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERRO]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCESSO]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[AVISO]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Verificar se Docker Compose está instalado
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    error "Docker Compose não está instalado!"
    exit 1
fi

# Verificar se arquivo .env existe
if [ ! -f ".env" ]; then
    error "Arquivo .env não encontrado!"
    info "Crie o arquivo .env com as variáveis necessárias"
    exit 1
fi

# Converter quebras de linha do Windows se necessário
if command -v dos2unix &> /dev/null; then
    dos2unix .env 2>/dev/null || true
else
    sed -i 's/\r$//' .env 2>/dev/null || true
fi

log "Iniciando deploy com Docker Compose..."

# Parar containers existentes
log "Parando containers existentes..."
docker-compose down 2>/dev/null || docker compose down 2>/dev/null || true

# Construir e iniciar
log "Construindo e iniciando containers..."
if docker compose version &> /dev/null; then
    docker compose up -d --build
else
    docker-compose up -d --build
fi

if [ $? -eq 0 ]; then
    success "✅ Deploy concluído com sucesso!"
    echo ""
    info "🌐 URLs de Acesso:"
    info "   Local: http://localhost:8000"
    
    # Tentar obter IP da máquina
    machine_ip=$(hostname -I | awk '{print $1}' 2>/dev/null || ip route get 1.1.1.1 | awk '{print $7; exit}' 2>/dev/null || echo "")
    if [ -n "$machine_ip" ]; then
        info "   Rede:  http://$machine_ip:8000"
    fi
    
    echo ""
    info "📋 Comandos úteis:"
    info "   Ver logs: docker-compose logs -f"
    info "   Parar: docker-compose down"
    info "   Reiniciar: docker-compose restart"
    echo ""
    info "🔐 Credenciais de Teste:"
    info "   Usuário: Opera"
    info "   Senha: Opera@2026"
else
    error "Falha no deploy!"
    exit 1
fi

