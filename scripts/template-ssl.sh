#!/bin/bash
# Script Template para Configuração SSL
# Copie este arquivo e substitua as variáveis conforme sua aplicação

set -e

# ============================================
# CONFIGURAÇÕES - ALTERE AQUI
# ============================================
DOMAIN="seu-dominio.com"                    # Seu domínio
EMAIL="seu-email@exemplo.com"                # Email para notificações
SERVICE_NAME="sua-app"                       # Nome do serviço no docker-compose.yml
APP_PORT="8000"                              # Porta interna da aplicação
NETWORK_NAME="app-network"                   # Nome da rede Docker
COMPOSE_FILE="docker-compose.yml"            # Arquivo docker-compose.yml

# ============================================
# NÃO ALTERAR ABAIXO (a menos que necessário)
# ============================================

echo "🔒 Configurando SSL/HTTPS para $DOMAIN..."
echo ""

# Verificar se o domínio está apontando para o servidor
echo "📋 Verificando DNS..."
IP_SERVIDOR=$(curl -s ifconfig.me 2>/dev/null || curl -s ipinfo.io/ip 2>/dev/null || echo "N/A")
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
mkdir -p config/nginx
mkdir -p certbot/conf
mkdir -p certbot/www
mkdir -p logs/nginx

# Parar containers se estiverem rodando
echo "🛑 Parando containers..."
docker-compose -f $COMPOSE_FILE down || true

# Iniciar Nginx temporário com configuração HTTP
echo "🚀 Iniciando Nginx temporário..."
docker-compose -f $COMPOSE_FILE up -d nginx $SERVICE_NAME

# Aguardar Nginx iniciar
echo "⏳ Aguardando Nginx iniciar..."
sleep 10

# Verificar se Nginx está respondendo
if ! curl -s http://localhost/.well-known/acme-challenge/test > /dev/null 2>&1; then
    echo "⚠️  Nginx pode não estar pronto. Aguardando mais 5 segundos..."
    sleep 5
fi

# Obter certificado SSL
echo "📜 Obtendo certificado SSL do Let's Encrypt..."
docker run --rm \
    -v "$(pwd)/certbot/conf:/etc/letsencrypt" \
    -v "$(pwd)/certbot/www:/var/www/certbot" \
    --network ${NETWORK_NAME//-/_} \
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
    echo ""
    echo "Verifique:"
    echo "  1. DNS está configurado corretamente"
    echo "  2. Porta 80 está aberta no firewall"
    echo "  3. Nginx está acessível em http://$DOMAIN"
    echo "  4. Location /.well-known/acme-challenge/ está configurado no nginx-http.conf"
    exit 1
fi

echo "✅ Certificado SSL obtido com sucesso!"

# Reiniciar containers com HTTPS
echo "🔄 Reiniciando containers com HTTPS..."
docker-compose -f $COMPOSE_FILE down
docker-compose -f $COMPOSE_FILE up -d

echo ""
echo "✅ SSL/HTTPS configurado com sucesso!"
echo ""
echo "🌐 Acesse: https://$DOMAIN"
echo ""
echo "📋 Próximos passos:"
echo "   1. Teste o acesso: curl -I https://$DOMAIN"
echo "   2. Configure renovação automática no crontab"
echo "   3. Verifique a segurança: https://www.ssllabs.com/ssltest/analyze.html?d=$DOMAIN"

