#!/bin/bash

# Script de Deploy - Portal Maestro com Nginx e HTTPS
# Uso: ./deploy-linux.sh [opções]
# 
# Versão: 2.0 - Com suporte a Nginx e HTTPS
# 
# Opções:
#   --build         Constrói a imagem Docker
#   --clean-build   Para containers, remove imagens e reconstrói
#   --start         Inicia os containers (Flask + Nginx)
#   --stop          Para os containers
#   --restart       Reinicia os containers
#   --status        Mostra status dos containers
#   --logs          Mostra logs dos containers
#   --full-deploy   Deploy completo: para, reconstrói e inicia tudo (Flask + Nginx + SSL)
#   --setup-ssl     Configura SSL/HTTPS com Let's Encrypt
#   --check-ports   Verifica configuração de portas no firewall

set -e

# Configurações
IMAGE_NAME="maestro-portal"
TAG="v1.0"
FULL_IMAGE_NAME="${IMAGE_NAME}:${TAG}"
CONTAINER_NAME="maestro-portal"
NGINX_CONTAINER="maestro-nginx"
TAR_FILE="maestro-portal-v1.0.tar"
PORT="8000"
DOMAIN="maestro.opera.security"
EMAIL="admin@opera.security"  # Altere se necessário
COMPOSE_FILE="docker-compose.yml"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Função para obter IP da máquina
get_machine_ip() {
    # Tentar diferentes métodos para obter o IP
    local ip=""
    
    # Método 1: hostname -I (Linux)
    if command -v hostname &> /dev/null; then
        ip=$(hostname -I | awk '{print $1}' 2>/dev/null)
    fi
    
    # Método 2: ip route (Linux)
    if [ -z "$ip" ] && command -v ip &> /dev/null; then
        ip=$(ip route get 1.1.1.1 | awk '{print $7; exit}' 2>/dev/null)
    fi
    
    # Método 3: ifconfig (fallback)
    if [ -z "$ip" ] && command -v ifconfig &> /dev/null; then
        ip=$(ifconfig | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1' | head -1)
    fi
    
    echo "$ip"
}

# Função para log
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

# Verificar se Docker está instalado
check_docker() {
    if ! command -v docker &> /dev/null; then
        error "Docker não está instalado. Instale o Docker primeiro."
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        error "Docker não está rodando. Inicie o serviço Docker."
        exit 1
    fi
    
    # Verificar Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        error "Docker Compose não está instalado. Instale o Docker Compose primeiro."
        exit 1
    fi
    
    success "Docker está funcionando"
}

# Verificar se Docker Compose está disponível
check_docker_compose() {
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    elif docker compose version &> /dev/null 2>&1; then
        COMPOSE_CMD="docker compose"
    else
        error "Docker Compose não encontrado!"
        exit 1
    fi
}

# Verificar estrutura de pastas
check_project_structure() {
    log "Verificando estrutura do projeto..."
    
    # Criar diretórios necessários se não existirem
    mkdir -p config/nginx
    mkdir -p config/ssl
    mkdir -p scripts
    mkdir -p docs
    mkdir -p logs/nginx
    mkdir -p certbot/conf
    mkdir -p certbot/www
    
    # Verificar se docker-compose.yml existe
    if [ ! -f "$COMPOSE_FILE" ]; then
        error "Arquivo $COMPOSE_FILE não encontrado!"
        exit 1
    fi
    
    # Verificar se configurações do Nginx existem
    if [ ! -f "config/nginx/nginx.conf" ]; then
        warning "config/nginx/nginx.conf não encontrado!"
        info "Certifique-se de que as configurações do Nginx estão presentes"
    fi
    
    success "Estrutura do projeto verificada"
}

# Verificar se arquivo .env existe
check_env_file() {
    if [ ! -f ".env" ]; then
        error "Arquivo .env não encontrado!"
        info "Crie o arquivo .env com as seguintes variáveis:"
        info "   SUPABASE_URL=..."
        info "   SUPABASE_SERVICE_ROLE_KEY=..."
        info "   SECRET_KEY=..."
        info ""
        info "Use o arquivo env_template.txt como referência"
        exit 1
    fi
    
    # Verificar se variáveis essenciais estão definidas
    if ! grep -q "SUPABASE_URL" .env || ! grep -q "SUPABASE_SERVICE_ROLE_KEY" .env || ! grep -q "SECRET_KEY" .env; then
        warning "Arquivo .env encontrado, mas algumas variáveis podem estar faltando"
        info "Certifique-se de que SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY e SECRET_KEY estão definidas"
    fi
}

# Verificar dependências de segurança
check_security_dependencies() {
    log "Verificando dependências de segurança..."
    
    if [ ! -f "requirements.txt" ]; then
        error "requirements.txt não encontrado!"
        exit 1
    fi
    
    # Verificar se as novas dependências de segurança estão presentes
    local missing_deps=0
    
    if ! grep -q "Flask-WTF" requirements.txt; then
        warning "Flask-WTF não encontrado em requirements.txt"
        missing_deps=$((missing_deps + 1))
    fi
    
    if ! grep -q "Flask-Limiter" requirements.txt; then
        warning "Flask-Limiter não encontrado em requirements.txt"
        missing_deps=$((missing_deps + 1))
    fi
    
    if ! grep -q "bleach" requirements.txt; then
        warning "bleach não encontrado em requirements.txt"
        missing_deps=$((missing_deps + 1))
    fi
    
    if [ $missing_deps -gt 0 ]; then
        error "Dependências de segurança faltando em requirements.txt!"
        info "Certifique-se de que requirements.txt contém:"
        info "  - Flask-WTF==1.2.1"
        info "  - WTForms==3.1.1"
        info "  - Flask-Limiter==3.5.0"
        info "  - bleach==6.1.0"
        exit 1
    fi
    
    success "Todas as dependências de segurança estão presentes"
    info "📦 Dependências de segurança:"
    info "   ✓ Flask-WTF (Proteção CSRF)"
    info "   ✓ Flask-Limiter (Rate Limiting)"
    info "   ✓ bleach (Sanitização HTML)"
}

# Construir imagem Docker
build_image() {
    log "Construindo imagem Docker..."
    
    # Verificar dependências de segurança
    check_security_dependencies
    
    # Verificar Docker Compose
    check_docker_compose
    
    # Verificar estrutura do projeto
    check_project_structure
    
    # Verificar se o Dockerfile existe
    if [ ! -f "Dockerfile" ]; then
        error "Dockerfile não encontrado!"
        exit 1
    fi
    
    # Verificar se requirements.txt existe
    if [ ! -f "requirements.txt" ]; then
        error "requirements.txt não encontrado!"
        exit 1
    fi
    
    info "Construindo imagem com Docker Compose..."
    info "🔒 Incluindo melhorias de segurança (CSRF, Rate Limiting, Validação)"
    
    # Construir imagem usando Docker Compose
    if $COMPOSE_CMD -f "$COMPOSE_FILE" build maestro-portal; then
        success "✅ Imagem construída com sucesso!"
        echo ""
        info "📦 Imagens criadas:"
        docker images | grep -E "$IMAGE_NAME|nginx" || true
        echo ""
        info "🔒 Melhorias de segurança incluídas:"
        info "   ✓ Proteção CSRF (Flask-WTF)"
        info "   ✓ Rate Limiting (Flask-Limiter)"
        info "   ✓ Validação de entrada"
        info "   ✓ Sanitização HTML (bleach)"
        info "   ✓ Logs de segurança"
        info "   ✓ Proteção SSRF no proxy"
    else
        error "❌ Falha ao construir a imagem"
        exit 1
    fi
}

# Build com limpeza completa
clean_build() {
    log "Iniciando build com limpeza completa..."
    
    check_docker_compose
    
    # Parar containers
    stop_containers
    
    # Remover imagens
    if docker images | grep -q "$IMAGE_NAME"; then
        log "Removendo imagens anteriores..."
        docker rmi "$FULL_IMAGE_NAME" 2>/dev/null || true
        success "Imagens anteriores removidas"
    fi
    
    # Limpar cache do Docker (opcional)
    log "Limpando cache do Docker..."
    docker system prune -f 2>/dev/null || true
    
    # Fazer build da nova imagem
    build_image
}

# Carregar imagem do arquivo .tar
load_image() {
    log "Carregando imagem do arquivo .tar..."
    
    if [ ! -f "$TAR_FILE" ]; then
        error "Arquivo $TAR_FILE não encontrado!"
        info "Arquivos .tar disponíveis:"
        ls -la *.tar 2>/dev/null || echo "   Nenhum arquivo .tar encontrado"
        echo ""
        info "Para criar o arquivo .tar, execute:"
        info "   docker save -o $TAR_FILE $FULL_IMAGE_NAME"
        exit 1
    fi
    
    info "Carregando $TAR_FILE..."
    docker load -i "$TAR_FILE"
    
    if [ $? -eq 0 ]; then
        success "Imagem carregada com sucesso!"
    else
        error "Erro ao carregar a imagem"
        exit 1
    fi
}

# Parar containers se existirem
stop_containers() {
    log "Parando containers..."
    
    # Parar usando docker-compose
    if [ -f "$COMPOSE_FILE" ]; then
        check_docker_compose
        $COMPOSE_CMD -f "$COMPOSE_FILE" down 2>/dev/null || true
        success "Containers parados via Docker Compose"
    else
        # Fallback: parar containers individualmente
        if docker ps -q -f name="$CONTAINER_NAME" | grep -q .; then
            docker stop "$CONTAINER_NAME" 2>/dev/null || true
            docker rm "$CONTAINER_NAME" 2>/dev/null || true
        fi
        
        if docker ps -q -f name="$NGINX_CONTAINER" | grep -q .; then
            docker stop "$NGINX_CONTAINER" 2>/dev/null || true
            docker rm "$NGINX_CONTAINER" 2>/dev/null || true
        fi
        
        success "Containers parados"
    fi
}

# Verificar se as portas estão disponíveis
check_ports() {
    log "Verificando portas 80 e 443..."
    
    local port_80_in_use=false
    local port_443_in_use=false
    
    if command -v ss &> /dev/null; then
        if ss -tuln | grep -q ":80 "; then
            port_80_in_use=true
        fi
        if ss -tuln | grep -q ":443 "; then
            port_443_in_use=true
        fi
    elif command -v netstat &> /dev/null; then
        if netstat -tuln | grep -q ":80 "; then
            port_80_in_use=true
        fi
        if netstat -tuln | grep -q ":443 "; then
            port_443_in_use=true
        fi
    fi
    
    if [ "$port_80_in_use" = true ] || [ "$port_443_in_use" = true ]; then
        warning "Algumas portas estão em uso:"
        [ "$port_80_in_use" = true ] && warning "  Porta 80 está em uso"
        [ "$port_443_in_use" = true ] && warning "  Porta 443 está em uso"
        info "Execute: $0 --stop (para parar containers existentes)"
        read -p "Continuar mesmo assim? (s/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Ss]$ ]]; then
            exit 1
        fi
    else
        success "Portas 80 e 443 estão disponíveis"
    fi
}

# Verificar configuração do firewall
check_firewall() {
    log "Verificando configuração de portas..."
    
    # Verificar se portas estão disponíveis no sistema (não em uso)
    local port_80_available=true
    local port_443_available=true
    
    if command -v ss &> /dev/null; then
        if ss -tuln | grep -q ":80 "; then
            port_80_available=false
        fi
        if ss -tuln | grep -q ":443 "; then
            port_443_available=false
        fi
    elif command -v netstat &> /dev/null; then
        if netstat -tuln | grep -q ":80 "; then
            port_80_available=false
        fi
        if netstat -tuln | grep -q ":443 "; then
            port_443_available=false
        fi
    fi
    
    if [ "$port_80_available" = false ] || [ "$port_443_available" = false ]; then
        warning "Algumas portas estão em uso no sistema:"
        [ "$port_80_available" = false ] && warning "  Porta 80 está em uso"
        [ "$port_443_available" = false ] && warning "  Porta 443 está em uso"
        info "Execute: $0 --stop (para parar containers existentes)"
    else
        success "Portas 80 e 443 estão disponíveis no sistema"
    fi
    
    # Aviso sobre firewall externo (Fortinet)
    echo ""
    warning "⚠️  FIREWALL EXTERNO (FORTINET):"
    info "   Você precisa abrir as portas 80 e 443 manualmente no Fortinet"
    info "   Configure as seguintes reglas no Fortinet:"
    echo ""
    echo "   Porta 80 (HTTP):"
    echo "     - Permitir tráfego TCP na porta 80"
    echo "     - Destino: IP do servidor ($(get_machine_ip || echo 'SEU_IP'))"
    echo ""
    echo "   Porta 443 (HTTPS):"
    echo "     - Permitir tráfego TCP na porta 443"
    echo "     - Destino: IP do servidor ($(get_machine_ip || echo 'SEU_IP'))"
    echo ""
    info "   ⚠️  IMPORTANTE: A porta 8000 NÃO deve estar exposta no Fortinet!"
    info "      Ela é apenas interna (dentro do Docker)"
    echo ""
    read -p "Portas já estão abertas no Fortinet? (s/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        warning "⚠️  Lembre-se de abrir as portas 80 e 443 no Fortinet antes de acessar a aplicação!"
    else
        success "Portas configuradas no Fortinet"
    fi
    echo ""
}

# Carregar variáveis do .env
load_env_vars() {
    if [ -f ".env" ]; then
        # Carrega variáveis do .env de forma segura, lidando com valores que contêm caracteres especiais
        while IFS= read -r line || [ -n "$line" ]; do
            # Remove espaços em branco, tabs e carriage returns (\r) no início e fim
            line=$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | tr -d '\r')
            # Ignora linhas vazias e comentários
            if [[ -n "$line" && ! "$line" =~ ^[[:space:]]*# ]]; then
                # Verifica se a linha contém um sinal de igual
                if [[ "$line" =~ ^[^=]+= ]]; then
                    # Extrai nome da variável e valor
                    var_name=$(echo "$line" | cut -d '=' -f 1 | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | tr -d '\r\n')
                    var_value=$(echo "$line" | cut -d '=' -f 2- | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | tr -d '\r\n')
                    # Remove aspas simples ou duplas se existirem no início e fim
                    var_value=$(echo "$var_value" | sed -e "s/^['\"]//" -e "s/['\"]$//")
                    # Exporta a variável apenas se o nome não estiver vazio
                    if [ -n "$var_name" ] && [ -n "$var_value" ]; then
                        eval "export ${var_name}=\"${var_value}\"" 2>/dev/null || export "$var_name=$var_value" 2>/dev/null || true
                    fi
                fi
            fi
        done < .env
    fi
}

# Iniciar containers com Docker Compose
start_containers() {
    log "Iniciando containers (Flask + Nginx)..."
    
    # Verificar estrutura do projeto
    check_project_structure
    
    # Verificar arquivo .env
    check_env_file
    
    # Verificar se as portas estão disponíveis
    check_ports
    
    # Verificar Docker Compose
    check_docker_compose
    
    # Parar containers existentes se houver
    stop_containers
    
    # Verificar se docker-compose.yml existe
    if [ ! -f "$COMPOSE_FILE" ]; then
        error "Arquivo $COMPOSE_FILE não encontrado!"
        exit 1
    fi
    
    # Carregar variáveis do .env usando método mais robusto
    # Primeiro tenta carregar com source (se o .env estiver no formato correto)
    if [ -f ".env" ]; then
        # Remove caracteres \r do arquivo temporariamente para leitura
        set -a
        # Usa um método mais direto: lê linha por linha e exporta
        while IFS='=' read -r key value || [ -n "$key" ]; do
            # Ignora comentários e linhas vazias
            [[ "$key" =~ ^#.*$ ]] && continue
            [[ -z "$key" ]] && continue
            
            # Remove espaços e caracteres de controle
            key=$(echo "$key" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | tr -d '\r\n')
            value=$(echo "$value" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | tr -d '\r\n')
            
            # Remove aspas se existirem
            value=$(echo "$value" | sed -e "s/^['\"]//" -e "s/['\"]$//")
            
            # Exporta se ambos existirem
            if [ -n "$key" ] && [ -n "$value" ]; then
                export "$key=$value" 2>/dev/null || true
            fi
        done < <(grep -v '^[[:space:]]*#' .env | grep '=')
        set +a
    fi
    
    # Limpar caracteres de controle das variáveis essenciais (remove \r e \n)
    SUPABASE_URL=$(echo "${SUPABASE_URL:-}" | tr -d '\r\n' | sed 's/[[:space:]]*$//')
    SUPABASE_SERVICE_ROLE_KEY=$(echo "${SUPABASE_SERVICE_ROLE_KEY:-}" | tr -d '\r\n' | sed 's/[[:space:]]*$//')
    SECRET_KEY=$(echo "${SECRET_KEY:-}" | tr -d '\r\n' | sed 's/[[:space:]]*$//')
    
    # Verificar se variáveis essenciais foram carregadas
    if [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_SERVICE_ROLE_KEY" ] || [ -z "$SECRET_KEY" ]; then
        error "Variáveis essenciais não foram carregadas do .env!"
        error "Certifique-se de que o arquivo .env contém:"
        error "  - SUPABASE_URL"
        error "  - SUPABASE_SERVICE_ROLE_KEY"
        error "  - SECRET_KEY"
        error ""
        error "💡 Dica: Use Docker Compose para deploy mais confiável:"
        error "   chmod +x deploy-compose.sh && ./deploy-compose.sh"
        exit 1
    fi
    
    # Criar diretórios necessários
    mkdir -p ./logs
    mkdir -p ./logs/nginx
    mkdir -p ./certbot/conf
    mkdir -p ./certbot/www
    
    # Iniciar containers com Docker Compose
    log "Iniciando containers com Docker Compose..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" up -d --build
    
    if [ $? -eq 0 ]; then
        success "Containers iniciados com sucesso!"
        echo ""
        info "📦 Containers em execução:"
        $COMPOSE_CMD -f "$COMPOSE_FILE" ps
        echo ""
        info "🌐 Aplicação disponível em:"
        info "   HTTP:  http://$DOMAIN (redireciona para HTTPS)"
        info "   HTTPS: https://$DOMAIN"
        echo ""
        warning "⚠️  IMPORTANTE - FIREWALL FORTINET:"
        warning "   1. Abra as portas 80 e 443 manualmente no Fortinet"
        warning "   2. Configure o DNS para apontar $DOMAIN para este servidor"
        warning "   3. Execute: $0 --setup-ssl (para configurar HTTPS)"
    else
        error "Erro ao iniciar os containers"
        exit 1
    fi
}

# Mostrar status dos containers
show_status() {
    log "Status dos containers:"
    echo ""
    
    check_docker_compose
    
    if [ -f "$COMPOSE_FILE" ]; then
        $COMPOSE_CMD -f "$COMPOSE_FILE" ps
        echo ""
        
        # Verificar se containers estão rodando
        if $COMPOSE_CMD -f "$COMPOSE_FILE" ps | grep -q "Up"; then
            success "Containers estão rodando"
            echo ""
            
            # Testar aplicação
            log "Testando aplicação..."
            if curl -f -s -k https://localhost/login &> /dev/null || curl -f -s http://localhost/login &> /dev/null; then
                success "Aplicação está respondendo corretamente"
                echo ""
                info "🌐 URLs de Acesso:"
                info "   HTTP:  http://$DOMAIN (redireciona para HTTPS)"
                info "   HTTPS: https://$DOMAIN"
                
                # Verificar se certificado SSL existe
                if [ -f "certbot/conf/live/$DOMAIN/fullchain.pem" ]; then
                    success "✅ Certificado SSL configurado"
                else
                    warning "⚠️  Certificado SSL não encontrado"
                    info "   Execute: $0 --setup-ssl (para configurar HTTPS)"
                fi
                echo ""
            else
                warning "Aplicação pode estar inicializando ainda..."
                info "Aguarde alguns segundos e execute: $0 --status"
            fi
        else
            warning "Containers não estão rodando"
            info "Execute: $0 --start (para iniciar)"
        fi
    else
        error "Arquivo $COMPOSE_FILE não encontrado!"
    fi
}

# Mostrar logs
show_logs() {
    check_docker_compose
    
    if [ -f "$COMPOSE_FILE" ]; then
        if $COMPOSE_CMD -f "$COMPOSE_FILE" ps | grep -q "Up"; then
            log "Mostrando logs dos containers (últimas 50 linhas):"
            $COMPOSE_CMD -f "$COMPOSE_FILE" logs --tail 50 -f
        else
            error "Containers não estão rodando"
            exit 1
        fi
    else
        error "Arquivo $COMPOSE_FILE não encontrado!"
        exit 1
    fi
}

# Configurar SSL/HTTPS
setup_ssl() {
    log "Configurando SSL/HTTPS..."
    
    check_docker
    check_docker_compose
    check_project_structure
    
    # Verificar DNS
    log "Verificando DNS..."
    DNS_IP=$(dig +short "$DOMAIN" 2>/dev/null | tail -n1 || echo "")
    if [ -z "$DNS_IP" ]; then
        warning "DNS não resolve para $DOMAIN"
        info "Configure o DNS antes de continuar:"
        info "  Tipo: A"
        info "  Nome: maestro"
        info "  Valor: $(get_machine_ip || echo 'SEU_IP')"
        echo ""
        read -p "DNS já está configurado? (s/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Ss]$ ]]; then
            error "Configure o DNS primeiro e tente novamente"
            exit 1
        fi
    else
        success "DNS resolve para: $DNS_IP"
    fi
    
    # Verificar se containers estão rodando
    if ! $COMPOSE_CMD -f "$COMPOSE_FILE" ps | grep -q "Up"; then
        warning "Containers não estão rodando. Iniciando..."
        start_containers
        sleep 10
    fi
    
    # Obter certificado SSL
    log "Obtendo certificado SSL do Let's Encrypt..."
    docker run --rm \
        -v "$(pwd)/certbot/conf:/etc/letsencrypt" \
        -v "$(pwd)/certbot/www:/var/www/certbot" \
        --network maestro_maestro-network \
        certbot/certbot certonly \
        --webroot \
        --webroot-path=/var/www/certbot \
        --email "$EMAIL" \
        --agree-tos \
        --no-eff-email \
        --force-renewal \
        -d "$DOMAIN" || {
        error "Erro ao obter certificado SSL"
        info "Verifique se:"
        info "  1. DNS está configurado corretamente"
        info "  2. Porta 80 está aberta no firewall"
        info "  3. Nginx está acessível"
        exit 1
    }
    
    # Verificar se certificado foi criado
    if [ ! -f "certbot/conf/live/$DOMAIN/fullchain.pem" ]; then
        error "Certificado SSL não foi criado"
        exit 1
    fi
    
    success "Certificado SSL obtido com sucesso!"
    
    # Reiniciar Nginx para usar HTTPS
    log "Reiniciando Nginx com HTTPS..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" restart nginx
    
    success "SSL/HTTPS configurado com sucesso!"
    echo ""
    info "🌐 Acesse: https://$DOMAIN"
    echo ""
    info "📝 Próximo passo: Configure renovação automática:"
    info "   crontab -e"
    info "   Adicione: 0 3 * * * $(pwd)/scripts/renovar-certificado.sh"
}

# Deploy completo
full_deploy() {
    log "Iniciando deploy completo (Flask + Nginx + SSL)..."
    echo ""
    
    check_docker
    check_docker_compose
    check_env_file
    check_project_structure
    
    # Verificar dependências de segurança
    check_security_dependencies
    
    # Verificar firewall
    check_firewall
    
    # Parar containers existentes
    stop_containers
    
    # Construir imagem
    log "Construindo imagem Docker..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" build maestro-portal
    
    # Iniciar containers
    start_containers
    
    # Aguardar aplicação inicializar
    log "Aguardando aplicação inicializar..."
    sleep 10
    
    # Mostrar status
    show_status
    
    echo ""
    info "✅ Deploy completo realizado!"
    echo ""
    warning "🔒 AÇÃO NECESSÁRIA - FIREWALL FORTINET:"
    info "   Abra as portas 80 e 443 no Fortinet manualmente:"
    echo ""
    echo "   Porta 80 (HTTP):"
    echo "     - Permitir TCP:80 → IP do servidor"
    echo ""
    echo "   Porta 443 (HTTPS):"
    echo "     - Permitir TCP:443 → IP do servidor"
    echo ""
    info "   ⚠️  NÃO abra a porta 8000 no Fortinet (ela é apenas interna)"
    echo ""
    info "📋 Próximos passos:"
    info "   1. Abrir portas 80 e 443 no Fortinet (manual)"
    info "   2. Configure o DNS para apontar $DOMAIN para este servidor"
    info "   3. Execute: $0 --setup-ssl (para configurar HTTPS)"
    info "   4. Configure renovação automática do certificado (crontab)"
    echo ""
    info "🔒 Segurança:"
    info "   • Proteção CSRF ativa"
    info "   • Rate Limiting: 5 tentativas/15min (login), 100 req/hora (API)"
    info "   • Validação de entrada ativa"
    info "   • Logs de segurança habilitados"
    info "   • Nginx como proxy reverso"
    echo ""
}

# Mostrar informações do sistema
show_system_info() {
    echo ""
    info "📊 Informações do Sistema:"
    info "   Arquivo TAR: $TAR_FILE"
    info "   Imagem: $FULL_IMAGE_NAME"
    info "   Container: $CONTAINER_NAME"
    info "   Porta: $HOST_PORT (externa) -> $PORT (interna)"
    
    local machine_ip=$(get_machine_ip)
    if [ -n "$machine_ip" ]; then
        info "   IP da máquina: $machine_ip"
    fi
    
    # Verificar arquivo .env
    if [ -f ".env" ]; then
        success "   Arquivo .env: ✓ encontrado"
    else
        warning "   Arquivo .env: ✗ não encontrado"
    fi
    echo ""
}

# Mostrar ajuda
show_help() {
    echo "🎼 Portal Maestro - Script de Deploy Linux"
    echo ""
    echo "✨ Sistema de autenticação avançado com Supabase"
    echo ""
    echo "Uso: $0 [opção]"
    echo ""
    echo "Opções:"
    echo "  --build         Constrói a imagem Docker"
    echo "  --clean-build   Para containers, remove imagens e reconstrói"
    echo "  --start         Inicia os containers (Flask + Nginx)"
    echo "  --stop          Para os containers"
    echo "  --restart       Reinicia os containers"
    echo "  --status        Mostra status dos containers"
    echo "  --logs          Mostra logs dos containers"
    echo "  --full-deploy   Deploy completo: para, reconstrói e inicia tudo"
    echo "  --setup-ssl     Configura SSL/HTTPS com Let's Encrypt"
    echo "  --check-ports   Verifica configuração de portas no firewall"
    echo "  --check-deps    Verifica dependências de segurança"
    echo "  --info          Mostra informações do sistema"
    echo "  --help          Mostra esta ajuda"
    echo ""
    echo "Exemplos:"
    echo "  $0 --full-deploy    # Deploy completo (Flask + Nginx)"
    echo "  $0 --setup-ssl      # Configurar HTTPS após deploy"
    echo "  $0 --start          # Iniciar containers"
    echo "  $0 --status         # Ver status"
    echo "  $0 --logs           # Ver logs"
    echo "  $0 --check-ports    # Verificar portas do firewall"
    echo ""
    echo "⚠️  IMPORTANTE:"
    echo "   • Certifique-se de que o arquivo .env está configurado"
    echo "   • O arquivo .env deve conter SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY e SECRET_KEY"
    echo "   • requirements.txt deve conter todas as dependências de segurança"
    echo ""
    echo "🔒 Melhorias de Segurança:"
    echo "   • Proteção CSRF (Flask-WTF)"
    echo "   • Rate Limiting (Flask-Limiter)"
    echo "   • Validação de entrada"
    echo "   • Sanitização HTML (bleach)"
    echo "   • Logs de segurança"
    echo ""
    show_system_info
}

# Função para verificar portas
check_ports_only() {
    log "Verificando configuração de portas..."
    echo ""
    
    # Verificar portas no sistema
    check_ports
    
    # Aviso sobre Fortinet
    echo ""
    warning "🔒 FIREWALL FORTINET (EXTERNO):"
    info "   Configure manualmente no Fortinet:"
    echo ""
    echo "   ✅ Porta 80 (HTTP) - ABRIR"
    echo "   ✅ Porta 443 (HTTPS) - ABRIR"
    echo "   ❌ Porta 8000 - NÃO ABRIR (apenas interna)"
    echo ""
    
    local machine_ip=$(get_machine_ip)
    if [ -n "$machine_ip" ]; then
        info "   IP do servidor: $machine_ip"
    fi
    
    echo ""
    info "Para mais informações sobre portas, consulte:"
    info "  docs/CONFIGURACAO_PORTAS.md"
}

# Main
case "${1:-}" in
    --build)
        check_docker
        check_docker_compose
        build_image
        ;;
    --clean-build)
        check_docker
        check_docker_compose
        clean_build
        ;;
    --load-image)
        check_docker
        load_image
        ;;
    --start)
        check_docker
        start_containers
        ;;
    --stop)
        check_docker
        stop_containers
        ;;
    --restart)
        check_docker
        check_docker_compose
        stop_containers
        start_containers
        ;;
    --status)
        show_status
        ;;
    --logs)
        show_logs
        ;;
    --full-deploy)
        full_deploy
        ;;
    --setup-ssl)
        setup_ssl
        ;;
    --check-ports)
        check_ports_only
        ;;
    --info)
        show_system_info
        ;;
    --check-deps)
        check_docker
        check_security_dependencies
        ;;
    --help)
        show_help
        ;;
    "")
        show_help
        ;;
    *)
        error "Opção inválida: $1"
        show_help
        exit 1
        ;;
esac

