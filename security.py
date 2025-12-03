"""
Módulo de Segurança - Maestro Portal
Implementa proteções críticas: CSRF, Rate Limiting, Validação, Logging
"""
from flask import request, session, g
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
import logging
import re
import os
from urllib.parse import urlparse
from bleach import clean
from functools import wraps
import time

# Configurar logging de segurança
security_logger = logging.getLogger('security')
security_logger.setLevel(logging.WARNING)

# Handler para arquivo de log de segurança (opcional)
if not security_logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '%(asctime)s [SECURITY] %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    security_logger.addHandler(handler)

# Função para obter IP real do cliente (atrás de proxy Nginx)
def get_real_ip():
    """Obtém o IP real do cliente, considerando headers de proxy"""
    # Verificar X-Real-IP primeiro (Nginx)
    if request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    # Verificar X-Forwarded-For (pode ter múltiplos IPs, pegar o primeiro)
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        # X-Forwarded-For pode ter múltiplos IPs separados por vírgula
        # O primeiro é o IP original do cliente
        return forwarded_for.split(',')[0].strip()
    # Fallback para remote_addr
    return request.remote_addr or '127.0.0.1'

# Instâncias globais (serão inicializadas em init_security)
csrf = CSRFProtect()
limiter = Limiter(
    key_func=get_real_ip,  # Usar função customizada para pegar IP real
    default_limits=["1000 per hour"],  # Limite padrão mais alto
    storage_uri="memory://",
    default_limits_per_method=True,  # Limites por método HTTP
    default_limits_exempt_when=lambda: False  # Não isentar por padrão
)

def init_security(app):
    """Inicializa todas as proteções de segurança"""
    # CSRF Protection
    csrf.init_app(app)
    # Nota: Rotas de proxy são isentas do CSRF usando @csrf.exempt diretamente
    # nas rotas, pois são apenas proxy para outras aplicações que têm seus
    # próprios mecanismos de segurança
    
    # Rate Limiting
    limiter.init_app(app)
    
    # Isentar rotas de proxy e recursos estáticos do rate limiting padrão
    # (elas têm muitas requisições legítimas ao carregar uma página)
    @limiter.request_filter
    def exempt_proxy_and_static():
        from flask import request
        # Isentar rotas de proxy (muitas requisições ao carregar página)
        if request.path.startswith('/proxy/'):
            return True
        # Isentar rota de API (apenas redirecionamento interno)
        if request.path.startswith('/api/'):
            return True
        # Isentar recursos estáticos
        if request.path.startswith('/static/'):
            return True
        # Isentar favicon
        if request.path == '/favicon.ico':
            return True
        # Isentar GET na rota de login (apenas visualização da página)
        # POST (tentativas de login) ainda serão limitadas pelo decorator
        if request.path == '/login' and request.method == 'GET':
            return True
        # Isentar GET na rota raiz (apenas visualização)
        if request.path == '/' and request.method == 'GET':
            return True
        return False
    
    # Configurar logging
    if not app.debug:
        security_logger.setLevel(logging.INFO)
    
    # Headers de segurança adicionais
    @app.after_request
    def security_headers(response):
        """Adiciona headers de segurança"""
        from flask import request
        
        # Não aplicar CSP restritivo em rotas de proxy (para não bloquear recursos das aplicações proxyadas)
        if not request.path.startswith('/proxy/'):
            # Content Security Policy relaxado para Safari/MacBooks funcionarem com HTTP
            # Safari é muito restritivo, então precisamos ser mais permissivos
            csp = (
                "default-src 'self' 'unsafe-inline' 'unsafe-eval' data: blob:; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://fonts.googleapis.com http: https:; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com http: https:; "
                "font-src 'self' https://fonts.gstatic.com data: http: https:; "
                "img-src 'self' data: blob: http: https:; "
                "connect-src 'self' http: https: ws: wss:; "
                "frame-src 'self' http: https:; "
                "frame-ancestors 'self'; "
                "object-src 'none'; "
                "base-uri 'self';"
            )
            response.headers['Content-Security-Policy'] = csp
        
        # Referrer Policy mais permissivo para Safari
        response.headers['Referrer-Policy'] = 'no-referrer-when-downgrade'
        
        # Permissions Policy (aplicar sempre)
        response.headers['Permissions-Policy'] = (
            'geolocation=(), microphone=(), camera=()'
        )
        
        return response

def validate_username(username):
    """Valida formato de username"""
    if not username or len(username) < 3:
        return False, "Username deve ter pelo menos 3 caracteres"
    if len(username) > 50:
        return False, "Username muito longo (máximo 50 caracteres)"
    # Permitir letras, números, pontos, underscores e hífens
    if not re.match(r'^[a-zA-Z0-9._-]+$', username):
        return False, "Username contém caracteres inválidos"
    return True, None

def validate_password(password):
    """Valida força da senha"""
    if not password or len(password) < 8:
        return False, "Senha deve ter pelo menos 8 caracteres"
    if len(password) > 128:
        return False, "Senha muito longa (máximo 128 caracteres)"
    # Verificar complexidade básica
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password)
    
    if not (has_upper and has_lower and (has_digit or has_special)):
        return False, "Senha deve conter letras maiúsculas, minúsculas e números ou caracteres especiais"
    
    return True, None

def sanitize_html(html_content):
    """Sanitiza HTML removendo conteúdo perigoso"""
    # Tags permitidas (básico - ajustar conforme necessário)
    allowed_tags = [
        'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'ul', 'ol', 'li', 'a', 'img', 'div', 'span', 'table', 'tr', 'td', 'th',
        'thead', 'tbody', 'tfoot'
    ]
    
    allowed_attributes = {
        'a': ['href', 'title'],
        'img': ['src', 'alt', 'title', 'width', 'height'],
        '*': ['class', 'id', 'style']
    }
    
    # Limpar HTML
    cleaned = clean(
        html_content,
        tags=allowed_tags,
        attributes=allowed_attributes,
        strip=True
    )
    
    return cleaned

def validate_proxy_url(url):
    """Valida URL do proxy para prevenir SSRF"""
    try:
        parsed = urlparse(url)
        
        # Apenas HTTP/HTTPS permitidos
        if parsed.scheme not in ['http', 'https']:
            return False, "Apenas HTTP e HTTPS são permitidos"
        
        # Lista de hosts permitidos (whitelist)
        allowed_hosts = os.getenv('ALLOWED_PROXY_HOSTS', '10.150.16.45,10.150.16.24').split(',')
        allowed_hosts = [h.strip() for h in allowed_hosts]
        
        host = parsed.hostname
        if not host:
            return False, "Host inválido"
        
        # Verificar se host está na whitelist
        if host not in allowed_hosts:
            security_logger.warning(f"Tentativa de acesso a host não autorizado: {host}")
            return False, "Host não autorizado"
        
        # Bloquear IPs privados/reservados (exceto os permitidos)
        if parsed.hostname in ['127.0.0.1', 'localhost', '0.0.0.0']:
            return False, "Acesso a localhost não permitido"
        
        return True, None
        
    except Exception as e:
        security_logger.error(f"Erro ao validar URL do proxy: {str(e)}")
        return False, "URL inválida"

def log_security_event(event_type, details, ip_address=None, user_id=None):
    """Registra eventos de segurança"""
    ip = ip_address or request.remote_addr
    user = user_id or session.get('user_id', 'anonymous')
    username = session.get('username', 'unknown')
    
    log_message = f"[{event_type}] IP: {ip}, User: {user} ({username}), Details: {details}"
    security_logger.warning(log_message)

def log_failed_login(username, reason):
    """Registra tentativa de login falhada"""
    log_security_event(
        'FAILED_LOGIN',
        f"Username: {username}, Reason: {reason}",
        user_id=None
    )

def log_successful_login(username):
    """Registra login bem-sucedido"""
    log_security_event(
        'SUCCESSFUL_LOGIN',
        f"Username: {username}",
        user_id=session.get('user_id')
    )

def log_proxy_access(app_key, path, status_code):
    """Registra acesso via proxy"""
    if status_code >= 400:
        log_security_event(
            'PROXY_ERROR',
            f"App: {app_key}, Path: {path}, Status: {status_code}",
            user_id=session.get('user_id')
        )

def rate_limit_login():
    """Decorator para rate limiting no login - apenas para POST (tentativas de login)"""
    # Limite mais permissivo: 30 tentativas por 15 minutos
    # GET (visualização da página) é isentado no request_filter
    # Este decorator aplica limite apenas quando o request_filter não isentar
    return limiter.limit(
        "30 per 15 minutes",
        error_message="Muitas tentativas de login. Tente novamente em 15 minutos."
    )

def rate_limit_api():
    """Decorator para rate limiting em APIs"""
    return limiter.limit("1000 per hour", error_message="Limite de requisições excedido.")

def rate_limit_proxy():
    """Decorator para rate limiting em proxy (muito mais permissivo)"""
    # Limite muito alto para não interferir com carregamento normal de páginas
    return limiter.limit("10000 per hour", error_message="Limite de requisições excedido.")

