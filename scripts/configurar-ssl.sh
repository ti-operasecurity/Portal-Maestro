#!/bin/bash
# Script para configurar SSL/HTTPS com Let's Encrypt no Maestro Portal
# Uso: ./configurar-ssl.sh

set -e

DOMAIN="maestro.opera.security"
EMAIL="admin@opera.security"  # Altere para seu email
COMPOSE_FILE="docker-compose.yml"

echo "🔒 Configurando SSL/HTTPS para $DOMAIN..."

# Verificar se o domínio está apontando para o servidor
echo "📋 Verificando DNS..."
IP_SERVIDOR=$(curl -s ifconfig.me)
echo "IP do servidor: $IP_SERVIDOR"
echo "Verifique se $DOMAIN está apontando para este IP"
read -p "O DNS está configurado corretamente? (s/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    echo "❌ Configure o DNS primeiro e tente novamente"
    exit 1
fi

# Criar diretórios necessários
echo "📁 Criando diretórios..."
mkdir -p config/ssl
mkdir -p certbot/conf
mkdir -p certbot/www

# Parar containers se estiverem rodando
echo "🛑 Parando containers..."
docker-compose -f $COMPOSE_FILE down || true

# Iniciar Nginx temporário com configuração HTTP
echo "🚀 Iniciando Nginx temporário..."
docker-compose -f $COMPOSE_FILE up -d nginx

# Aguardar Nginx iniciar
sleep 5

# Obter certificado SSL
echo "📜 Obtendo certificado SSL do Let's Encrypt..."
docker run --rm \
    -v "$(pwd)/certbot/conf:/etc/letsencrypt" \
    -v "$(pwd)/certbot/www:/var/www/certbot" \
    certbot/certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    --force-renewal \
    -d $DOMAIN

# Verificar se o certificado foi criado
if [ ! -f "certbot/conf/live/$DOMAIN/fullchain.pem" ]; then
    echo "❌ Erro ao obter certificado SSL"
    exit 1
fi

echo "✅ Certificado SSL obtido com sucesso!"

# Atualizar configuração do Nginx para HTTPS
echo "⚙️ Atualizando configuração do Nginx..."
# O nginx.conf já está configurado para HTTPS

# Reiniciar containers com HTTPS
echo "🔄 Reiniciando containers com HTTPS..."
docker-compose -f $COMPOSE_FILE down
docker-compose -f $COMPOSE_FILE up -d

echo "✅ SSL/HTTPS configurado com sucesso!"
echo "🌐 Acesse: https://$DOMAIN"
echo ""
echo "📝 Próximos passos:"
echo "1. Configure renovação automática do certificado (crontab)"
echo "2. Teste o acesso em: https://$DOMAIN"
echo "3. Verifique se o domínio é mantido (não redireciona para IP)"

