#!/bin/bash
# Script completo de deploy com HTTPS
# Uso: ./deploy-completo.sh

set -e

DOMAIN="maestro.opera.security"
EMAIL="admin@opera.security"  # Altere para seu email

echo "🚀 Deploy completo do Maestro Portal"
echo "===================================="
echo ""

# Verificar se está na pasta correta
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Erro: Execute este script na pasta raiz do projeto"
    exit 1
fi

# Verificar se Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "❌ Docker não está instalado"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose não está instalado"
    exit 1
fi

# Verificar DNS
echo "📋 Verificando DNS..."
DNS_IP=$(dig +short $DOMAIN | tail -n1)
if [ -z "$DNS_IP" ]; then
    echo "⚠️  Aviso: DNS não resolve para $DOMAIN"
    echo "   Configure o DNS antes de continuar"
    read -p "Continuar mesmo assim? (s/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        exit 1
    fi
else
    echo "✅ DNS resolve para: $DNS_IP"
fi

# Criar diretórios necessários
echo "📁 Criando diretórios..."
mkdir -p certbot/conf
mkdir -p certbot/www
mkdir -p logs/nginx
mkdir -p config/ssl

# Verificar se .env existe
if [ ! -f ".env" ]; then
    echo "⚠️  Arquivo .env não encontrado!"
    echo "   Criando .env a partir do template..."
    if [ -f "env_template.txt" ]; then
        cp env_template.txt .env
        echo "   ⚠️  Edite o arquivo .env com suas configurações antes de continuar"
        read -p "Pressione Enter após editar o .env..."
    else
        echo "   ❌ Template não encontrado. Crie o arquivo .env manualmente"
        exit 1
    fi
fi

# Parar containers existentes
echo "🛑 Parando containers existentes..."
docker-compose down 2>/dev/null || true

# Build da aplicação
echo "🔨 Construindo imagem da aplicação..."
docker-compose build maestro-portal

# Verificar se certificado SSL existe
if [ ! -f "certbot/conf/live/$DOMAIN/fullchain.pem" ]; then
    echo "🔒 Certificado SSL não encontrado"
    echo "   Configurando SSL com Let's Encrypt..."
    
    # Iniciar Nginx temporário
    echo "🚀 Iniciando Nginx temporário..."
    docker-compose up -d nginx maestro-portal
    
    # Aguardar serviços iniciarem
    echo "⏳ Aguardando serviços iniciarem..."
    sleep 10
    
    # Obter certificado
    echo "📜 Obtendo certificado SSL..."
    docker run --rm \
        -v "$(pwd)/certbot/conf:/etc/letsencrypt" \
        -v "$(pwd)/certbot/www:/var/www/certbot" \
        --network maestro_maestro-network \
        certbot/certbot certonly \
        --webroot \
        --webroot-path=/var/www/certbot \
        --email $EMAIL \
        --agree-tos \
        --no-eff-email \
        --force-renewal \
        -d $DOMAIN || {
        echo "❌ Erro ao obter certificado SSL"
        echo "   Verifique se:"
        echo "   1. DNS está configurado corretamente"
        echo "   2. Porta 80 está aberta no firewall"
        echo "   3. Nginx está acessível"
        exit 1
    }
    
    # Reiniciar Nginx com HTTPS
    echo "🔄 Reiniciando Nginx com HTTPS..."
    docker-compose restart nginx
else
    echo "✅ Certificado SSL já existe"
    # Iniciar todos os serviços
    echo "🚀 Iniciando serviços..."
    docker-compose up -d
fi

# Aguardar serviços iniciarem
echo "⏳ Aguardando serviços iniciarem..."
sleep 5

# Verificar saúde dos serviços
echo "🏥 Verificando saúde dos serviços..."
if docker-compose ps | grep -q "Up"; then
    echo "✅ Serviços iniciados com sucesso!"
else
    echo "❌ Erro ao iniciar serviços"
    docker-compose logs
    exit 1
fi

# Mostrar status
echo ""
echo "===================================="
echo "✅ Deploy concluído!"
echo ""
echo "🌐 Acesse: https://$DOMAIN"
echo ""
echo "📋 Próximos passos:"
echo "   1. Configure renovação automática do certificado:"
echo "      crontab -e"
echo "      Adicione: 0 3 * * * $(pwd)/scripts/renovar-certificado.sh"
echo ""
echo "   2. Verifique os logs:"
echo "      docker-compose logs -f"
echo ""
echo "   3. Teste o acesso:"
echo "      curl -I https://$DOMAIN"
echo ""

