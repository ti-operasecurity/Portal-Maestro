#!/bin/bash
# Script para renovar certificado SSL automaticamente
# Adicione ao crontab: 0 3 * * * /caminho/para/renovar-certificado.sh

set -e

DOMAIN="maestro.opera.security"
COMPOSE_FILE="docker-compose.yml"

echo "🔄 Renovando certificado SSL para $DOMAIN..."

# Renovar certificado
docker run --rm \
    -v "$(pwd)/certbot/conf:/etc/letsencrypt" \
    -v "$(pwd)/certbot/www:/var/www/certbot" \
    certbot/certbot renew \
    --quiet

# Recarregar Nginx se certificado foi renovado
if [ $? -eq 0 ]; then
    echo "🔄 Recarregando Nginx..."
    docker-compose -f $COMPOSE_FILE exec -T nginx nginx -s reload || true
    echo "✅ Certificado renovado e Nginx recarregado!"
else
    echo "ℹ️ Certificado ainda válido ou erro na renovação"
fi

