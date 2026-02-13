#!/bin/bash
# Renovação do certificado SSL (Let's Encrypt) para maestro.opera.security
# O Certbot renova automaticamente quando o certificado está a ~30 dias do vencimento.
# Uso: manual ou via cron (veja instruções no final do script ou em docs).
# Requer: Docker, containers maestro rodando, porta 80 acessível.

set -e

# Em cron, PATH pode ser mínimo; garantir que docker está disponível
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH"

# Ir para a raiz do projeto
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

DOMAIN="maestro.opera.security"
COMPOSE_FILE="docker-compose.yml"
LOG_FILE="${ROOT_DIR}/logs/certbot-renewal.log"
TIMEOUT_CERTBOT=400

# Criar pasta de logs se não existir
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Docker Compose
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
else
    log "[ERRO] Docker Compose não encontrado."
    exit 1
fi

# Verificar se os containers estão rodando
if ! $COMPOSE_CMD -f "$COMPOSE_FILE" ps 2>/dev/null | grep -q "Up"; then
    log "[AVISO] Containers não estão rodando. Inicie com: ./deploy-linux.sh --start"
    exit 1
fi

# Renovar certificado (Certbot só renova se faltar ~30 dias ou menos para vencer)
log "Verificando renovação do certificado para $DOMAIN..."
if timeout "$TIMEOUT_CERTBOT" docker run --rm \
    -v "$(pwd)/certbot/conf:/etc/letsencrypt" \
    -v "$(pwd)/certbot/www:/var/www/certbot" \
    --network maestro_maestro-network \
    certbot/certbot renew \
    --webroot \
    --webroot-path=/var/www/certbot \
    --quiet; then
    log "Reiniciando Nginx para carregar certificados..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" restart nginx >> "$LOG_FILE" 2>&1
    log "Concluído (certificado renovado ou ainda válido)."
else
    log "[ERRO] Falha na renovação ou timeout. Verifique: $LOG_FILE"
    exit 1
fi
