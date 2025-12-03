from flask import Flask, render_template, request, redirect, url_for, session, flash, Response, stream_with_context
import os
import requests
from io import BytesIO
from auth import auth_manager, login_required, init_auth
from security import (
    init_security, csrf, limiter, validate_username, validate_password,
    sanitize_html, validate_proxy_url, log_failed_login, log_successful_login,
    log_proxy_access, rate_limit_login, rate_limit_api
)
from http_pool import http_pool
from monitoring import record_request_time, get_metrics, log_performance_summary
from functools import wraps
from urllib.parse import urljoin, urlparse
import logging
from datetime import datetime, timedelta
import atexit

# Configurar logging para debug de acesso externo
# Configurar apenas se não houver handlers (evita duplicação)
root_logger = logging.getLogger()
if not root_logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

# Logger específico para acesso (sempre logar)
access_logger = logging.getLogger('maestro.access')
access_logger.setLevel(logging.INFO)
# Garantir que tenha handler
if not access_logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] maestro.access: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    access_logger.addHandler(handler)
    access_logger.setLevel(logging.INFO)

app = Flask(__name__)

# Configurações para aceitar qualquer host/domínio (acesso externo)
# IMPORTANTE: Necessário para funcionar com domínio externo no MacBook
app.config['SERVER_NAME'] = None  # Aceita qualquer host/domínio
# PREFERRED_URL_SCHEME será detectado dinamicamente no before_request
app.config['PREFERRED_URL_SCHEME'] = 'https'  # Padrão HTTPS quando atrás de Nginx

# Registrar função para log de performance ao encerrar
atexit.register(log_performance_summary)

# Inicializa autenticação
init_auth(app)

# Inicializa segurança (CSRF, Rate Limiting, etc.)
init_security(app)

# Expor CSRF token nos templates
@app.context_processor
def inject_csrf():
    """Injeta função CSRF token em todos os templates"""
    from flask_wtf.csrf import generate_csrf
    return dict(csrf_token=lambda: generate_csrf())

# Middleware para log de requisições (debug para MacBooks)
@app.before_request
def log_request_info():
    """Log informações da requisição para debug (especialmente MacBooks)"""
    # Atualizar esquema baseado no header do proxy
    if request.headers.get('X-Forwarded-Proto') == 'https':
        app.config['PREFERRED_URL_SCHEME'] = 'https'
    
    # Sempre logar informações importantes para debug de acesso externo
    access_logger.info(
        f"Requisição: {request.method} {request.path} | "
        f"Host: {request.headers.get('Host', 'N/A')} | "
        f"Origin: {request.headers.get('Origin', 'N/A')} | "
        f"Remote: {request.remote_addr} | "
        f"Scheme: {request.headers.get('X-Forwarded-Proto', 'http')} | "
        f"User-Agent: {request.headers.get('User-Agent', 'N/A')[:80]}"
    )

# Adicionar headers para compatibilidade com Safari/macOS e performance
@app.after_request
def add_headers(response):
    """Adiciona headers HTTP para compatibilidade com Safari/macOS e otimização"""
    # Não aplicar headers restritivos em rotas de proxy
    # (deixar a aplicação proxyada funcionar normalmente)
    if request.path.startswith('/proxy/'):
        # Headers otimizados para proxy - melhor compatibilidade com MacBooks
        response.headers['Connection'] = 'keep-alive'
        response.headers['Keep-Alive'] = 'timeout=10, max=1000'
        # CORS permissivo para evitar problemas em MacBooks
        if 'Access-Control-Allow-Origin' not in response.headers:
            response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, PATCH, OPTIONS, HEAD'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        # Headers para evitar problemas de cache em MacBooks
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    
    # Headers para recursos estáticos (cache otimizado)
    if request.path.startswith('/static/'):
        # Cache de recursos estáticos por 1 hora
        response.headers['Cache-Control'] = 'public, max-age=3600, must-revalidate'
        # Usar UTC para compatibilidade
        from datetime import timezone
        try:
            expires = (datetime.now(timezone.utc) + timedelta(hours=1)).strftime('%a, %d %b %Y %H:%M:%S GMT')
        except:
            # Fallback para versões antigas do Python
            expires = (datetime.utcnow() + timedelta(hours=1)).strftime('%a, %d %b %Y %H:%M:%S GMT')
        response.headers['Expires'] = expires
        response.headers['Connection'] = 'keep-alive'
        response.headers['Keep-Alive'] = 'timeout=10, max=1000'
        return response
    
    # Headers para rotas do Maestro (não proxy)
    # Headers para evitar problemas de cache e conexão
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    # Headers para compatibilidade com Safari/MacBooks (HTTP sem SSL)
    # Safari é muito restritivo, então precisamos ser mais permissivos
    response.headers['X-Content-Type-Options'] = 'nosniff'
    # X-Frame-Options mais permissivo para Safari
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '0'  # Desabilitar para evitar problemas no Safari
    
    # CORS muito permissivo para MacBooks/Safari funcionarem com HTTP
    # Safari bloqueia requisições cross-origin mesmo em HTTP se CORS não estiver correto
    origin = request.headers.get('Origin')
    host = request.headers.get('Host', '')
    
    # Aceitar qualquer origem para acesso externo (domínio ou IP)
    # MacBooks podem ter problemas com validação de origem
    if origin:
        response.headers['Access-Control-Allow-Origin'] = origin
    else:
        # Se não houver Origin, permitir qualquer origem
        response.headers['Access-Control-Allow-Origin'] = '*'
    
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, PATCH, OPTIONS, HEAD'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, Accept, Origin, Host'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Access-Control-Max-Age'] = '3600'
    response.headers['Vary'] = 'Origin, Host'  # Incluir Host no Vary para MacBooks
    
    # Header adicional para MacBooks com domínio externo
    if host:
        response.headers['X-Requested-Host'] = host
    
    # Manter conexão aberta (ajuda com ERR_EMPTY_RESPONSE em MacBooks)
    response.headers['Connection'] = 'keep-alive'
    response.headers['Keep-Alive'] = 'timeout=10, max=1000'
    
    # Headers adicionais para MacBooks/Safari
    response.headers['Accept-Ranges'] = 'bytes'
    # Safari precisa deste header para funcionar corretamente
    response.headers['X-WebKit-CSP'] = "default-src 'self' 'unsafe-inline' 'unsafe-eval' data: blob: http: https:"
    
    return response

# Configurações das aplicações
# Ordem: 3 cards no topo (maiores) + 4 cards embaixo (menores)
APLICACOES = [
    # Topo - 3 cards maiores
    {
        'nome': 'Monitoração Produtiva',
        'url': 'http://10.150.16.45:8082/',
        'url_proxy': '/proxy/painel-monitoracao',  # URL através do proxy
        'icone': '📊',
        'cor': '#3b82f6',  # Azul vibrante
        'tamanho': 'grande'  # Card grande no topo
    },
    {
        'nome': 'Dashboard de Perdas',
        'url': 'http://10.150.16.45:5253/',
        'url_proxy': '/proxy/dashboard-perdas',
        'icone': '📉',
        'cor': '#ef4444',  # Vermelho para alertas/perdas
        'tamanho': 'grande'  # Card grande no topo
    },
    {
        'nome': 'BUFFER do FORNO',
        'url': 'http://10.150.16.45:4300/buffer',
        'url_proxy': '/proxy/buffer-forno',
        'icone': '🔄',
        'cor': '#14b8a6',  # Teal para buffer/produção
        'tamanho': 'grande'  # Card grande no topo
    },
    # Embaixo - 4 cards menores
    {
        'nome': 'Monitoramento de Fornos',
        'url': 'http://10.150.16.45:8081/',
        'url_proxy': '/proxy/monitoramento-fornos',
        'icone': '🔥',
        'cor': '#f59e0b',  # Laranja para calor/fornos
        'tamanho': 'pequeno'  # Card pequeno embaixo
    },
    {
        'nome': 'Robô Logistica',
        'url': 'http://10.150.16.45:8088/',
        'url_proxy': '/proxy/robo-logistica',
        'icone': '🤖',
        'cor': '#8b5cf6',  # Roxo para tecnologia
        'tamanho': 'pequeno'  # Card pequeno embaixo
    },
    {
        'nome': 'Monitoramento Autoclaves',
        'url': 'http://10.150.16.45:8080/',
        'url_proxy': '/proxy/monitoramento-autoclaves',
        'icone': '⚙️',
        'cor': '#10b981',  # Verde para processos
        'tamanho': 'pequeno'  # Card pequeno embaixo
    },
    {
        'nome': 'Aging de Estoque',
        'url': 'http://10.150.16.24:8079/',
        'url_proxy': '/proxy/aging-estoque',
        'icone': '📦',
        'cor': '#06b6d4',  # Ciano para estoque
        'tamanho': 'pequeno'  # Card pequeno embaixo
    }
]

# Mapeamento de rotas proxy para URLs reais
PROXY_ROUTES = {
    'painel-monitoracao': 'http://10.150.16.45:8082',
    'dashboard-perdas': 'http://10.150.16.45:5253',
    'monitoramento-fornos': 'http://10.150.16.45:8081',
    'robo-logistica': 'http://10.150.16.45:8088',
    'monitoramento-autoclaves': 'http://10.150.16.45:8080',
    'aging-estoque': 'http://10.150.16.24:8079',
    'buffer-forno': 'http://10.150.16.45:4300'
}

# Configuração: usar proxy ou redirecionamento direto
# Se True, aplicações são acessadas através do proxy (recomendado para acesso externo)
# Se False, aplicações são acessadas diretamente (requer portas expostas)
USE_PROXY = os.getenv('USE_PROXY', 'True').lower() == 'true'

@app.route('/login', methods=['GET', 'POST', 'OPTIONS'])
@rate_limit_login()
@record_request_time
def login():
    """Rota de login com proteção de segurança"""
    # Tratar preflight CORS para MacBooks/Safari
    if request.method == 'OPTIONS':
        response = Response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Max-Age'] = '3600'
        return response
    
    # Se já estiver logado, redireciona para home
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        # Validação de entrada
        if not username or not password:
            flash('Por favor, preencha todos os campos.', 'error')
            return render_template('login.html')
        
        # Validar formato de username
        username_valid, username_error = validate_username(username)
        if not username_valid:
            log_failed_login(username, f"Formato inválido: {username_error}")
            flash('Credenciais inválidas.', 'error')  # Não revelar detalhes
            return render_template('login.html')
        
        # Autentica usuário
        result = auth_manager.authenticate(username, password)
        
        if result['success']:
            # Cria sessão
            try:
                session['user_id'] = result['user']['id']
                session['username'] = result['user']['username']
                session.permanent = True
                # Força salvamento da sessão
                session.modified = True
                
                log_successful_login(username)
                flash('Login realizado com sucesso!', 'success')
                return redirect(url_for('index'))
            except Exception as e:
                # Log do erro de sessão
                logging.error(f"Erro ao criar sessão: {str(e)}")
                log_failed_login(username, f"Erro de sessão: {str(e)}")
                flash('Erro ao criar sessão. Tente novamente.', 'error')
        else:
            # Log do erro de autenticação
            log_failed_login(username, result.get('message', 'Credenciais inválidas'))
            flash(result['message'], 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Rota de logout"""
    session.clear()
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('login'))

@app.route('/favicon.ico')
def favicon():
    """Rota para favicon - retorna 204 para evitar 404"""
    from flask import Response
    return Response(status=204)

@app.route('/health')
@app.route('/healthcheck')
def health_check():
    """Rota de health check - não requer autenticação, útil para testar acesso externo"""
    from flask import jsonify
    import socket
    
    # Informações básicas do servidor
    hostname = socket.gethostname()
    host_info = {
        'status': 'ok',
        'hostname': hostname,
        'host': request.headers.get('Host', 'N/A'),
        'remote_addr': request.remote_addr,
        'origin': request.headers.get('Origin', 'N/A'),
        'user_agent': request.headers.get('User-Agent', 'N/A')[:100],
        'timestamp': datetime.utcnow().isoformat()
    }
    
    return jsonify(host_info), 200

@app.route('/', methods=['GET', 'OPTIONS'])
@login_required
@record_request_time
def index():
    """Rota principal - protegida"""
    # Tratar preflight CORS para MacBooks/Safari
    if request.method == 'OPTIONS':
        response = Response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        return response
    # Preparar aplicações com URL correta (proxy ou direta)
    aplicacoes_preparadas = []
    for app in APLICACOES:
        app_copy = app.copy()
        if USE_PROXY and 'url_proxy' in app:
            app_copy['url_final'] = app['url_proxy']
            app_copy['target_blank'] = False
        else:
            app_copy['url_final'] = app['url']
            app_copy['target_blank'] = True
        aplicacoes_preparadas.append(app_copy)
    
    return render_template('index.html', aplicacoes=aplicacoes_preparadas)

@app.route('/api/<path:api_path>')
@login_required
@csrf.exempt  # Isentar do CSRF - é apenas um redirecionamento interno
# Sem rate limiting aqui - é apenas um redirecionamento interno
def proxy_api(api_path):
    """
    Intercepta requisições de API e redireciona para o proxy correto
    baseado no referer (página de origem)
    """
    referer = request.headers.get('Referer', '')
    
    # Tentar identificar qual aplicação proxy está sendo usada
    for app_key, target_url in PROXY_ROUTES.items():
        proxy_base = f'/proxy/{app_key}'
        if proxy_base in referer:
            # Redirecionar para a rota de proxy correta
            return redirect(f'{proxy_base}/api/{api_path}' + ('?' + request.query_string.decode('utf-8') if request.query_string else ''), code=307)
    
    # Se não conseguir identificar, retornar 404
    return Response('API não encontrada. Acesse através de uma aplicação proxy.', status=404)

@app.route('/proxy/<app_key>/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD'])
@app.route('/proxy/<app_key>/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD'])
@csrf.exempt  # Isentar do CSRF - é apenas um proxy para outras aplicações
@record_request_time
def proxy_app(app_key, path):
    """
    Proxy reverso para as aplicações internas
    Acessa aplicações através do Maestro sem expor portas diretamente
    """
    # Tratar preflight CORS para MacBooks/Safari (antes de verificar login)
    if request.method == 'OPTIONS':
        response = Response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, PATCH, OPTIONS, HEAD'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, Accept, Origin'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Max-Age'] = '3600'
        return response
    
    # Verificar login apenas para métodos que não sejam OPTIONS
    if 'user_id' not in session:
        flash('Você precisa fazer login para acessar esta página.', 'warning')
        return redirect(url_for('login'))
    
    if app_key not in PROXY_ROUTES:
        logging.warning(f"Tentativa de acesso a proxy inválido: {app_key}")
        flash('Aplicação não encontrada.', 'error')
        return redirect(url_for('index'))
    
    target_url = PROXY_ROUTES[app_key]
    
    # Validar URL do proxy (prevenir SSRF)
    url_valid, url_error = validate_proxy_url(target_url)
    if not url_valid:
        logging.error(f"URL do proxy inválida: {target_url} - {url_error}")
        flash('Erro de configuração. Entre em contato com o administrador.', 'error')
        return redirect(url_for('index'))
    
    # Construir URL completa
    # Aplicação buffer-forno precisa redirecionar para /buffer quando path estiver vazio
    # ou quando o path já começa com buffer (para evitar duplicação)
    if app_key == 'buffer-forno':
        if not path:
            full_url = urljoin(target_url, '/buffer')
        elif path.startswith('buffer'):
            # Se o path já começa com buffer, usar diretamente (ex: buffer/lookup, buffer/data)
            full_url = urljoin(target_url, '/' + path)
        else:
            # Se o path não começa com buffer, adicionar /buffer antes
            full_url = urljoin(target_url, '/buffer/' + path)
    elif path:
        full_url = urljoin(target_url + '/', path)
    else:
        full_url = target_url + '/'
    
    # Adicionar query string se houver
    if request.query_string:
        full_url += '?' + request.query_string.decode('utf-8')
    
    try:
        # Fazer requisição para a aplicação interna
        method = request.method
        headers = dict(request.headers)
        
        # Remover headers que não devem ser repassados
        # IMPORTANTE: Não remover Host completamente - pode causar problemas no MacBook
        # Apenas ajustar se necessário
        original_host = headers.get('Host', '')
        headers.pop('Content-Length', None)
        headers.pop('Connection', None)
        
        # Manter Host original para requisições internas (ajuda com MacBooks)
        # Mas remover apenas se for o host do Maestro para evitar confusão
        if 'Host' in headers:
            # Se o Host for do próprio Maestro, remover para não confundir aplicação destino
            host_value = headers.get('Host', '')
            if 'maestro' in host_value.lower() or '8000' in host_value:
                headers.pop('Host', None)
            # Caso contrário, manter o Host original
        
        # Preparar dados da requisição
        # Para POST/PUT/PATCH, usar form data se disponível, senão usar raw data
        if method in ['POST', 'PUT', 'PATCH']:
            # Verificar se é form data (application/x-www-form-urlencoded ou multipart/form-data)
            content_type = headers.get('Content-Type', '').lower()
            if 'multipart/form-data' in content_type:
                # Para multipart, usar form e files separadamente
                data = request.form.to_dict()
                # Preparar arquivos para requests
                files = {}
                for key, file_storage in request.files.items():
                    if file_storage.filename:
                        # Resetar o stream para o início
                        file_storage.seek(0)
                        # Ler conteúdo e criar BytesIO para requests
                        file_content = file_storage.read()
                        file_obj = BytesIO(file_content)
                        files[key] = (file_storage.filename, file_obj, file_storage.content_type)
                        # Resetar novamente caso seja necessário ler depois
                        file_storage.seek(0)
            elif 'application/x-www-form-urlencoded' in content_type:
                # Para form-urlencoded, usar apenas form data
                data = request.form.to_dict()
                files = None
            else:
                # Para outros tipos (JSON, XML, etc.), usar raw data
                data = request.get_data()
                files = None
        else:
            # Para GET, DELETE, etc., usar query params
            data = None
            files = None
        
        params = request.args.to_dict()
        
        # Usar pool de conexões HTTP para melhor performance
        http_session = http_pool.get_session(target_url)
        
        # Fazer requisição usando pool de conexões
        response = http_session.request(
            method=method,
            url=full_url,
            headers=headers,
            data=data,
            files=files,
            params=params,
            stream=True,
            timeout=30,
            allow_redirects=False
        )
        
        # Preparar resposta
        def generate():
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk
        
        # Headers da resposta
        response_headers = dict(response.headers)
        
        # Remover headers que não devem ser repassados
        response_headers.pop('Content-Encoding', None)
        response_headers.pop('Transfer-Encoding', None)
        response_headers.pop('Connection', None)
        response_headers.pop('Content-Length', None)  # Será recalculado
        
        # Remover CSP da aplicação proxyada (vamos controlar isso no Maestro)
        response_headers.pop('Content-Security-Policy', None)
        response_headers.pop('X-Content-Security-Policy', None)
        response_headers.pop('X-WebKit-CSP', None)
        
        # Garantir que CORS não bloqueie (se necessário)
        if 'Access-Control-Allow-Origin' not in response_headers:
            response_headers['Access-Control-Allow-Origin'] = '*'
        
        # Preservar MIME type correto baseado na extensão do arquivo
        # Isso é importante para CSS, JS, imagens, etc.
        content_type = response_headers.get('Content-Type', '').lower()
        
        # Se não houver Content-Type ou for genérico, tentar detectar pelo path
        if not content_type or 'text/html' in content_type or 'application/octet-stream' in content_type:
            path_lower = path.lower()
            if path_lower.endswith('.css'):
                content_type = 'text/css'
                response_headers['Content-Type'] = 'text/css; charset=utf-8'
            elif path_lower.endswith('.js'):
                content_type = 'application/javascript'
                response_headers['Content-Type'] = 'application/javascript; charset=utf-8'
            elif path_lower.endswith('.json'):
                content_type = 'application/json'
                response_headers['Content-Type'] = 'application/json; charset=utf-8'
            elif path_lower.endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.webp')):
                # Preservar MIME type original da imagem
                if 'image/' not in content_type:
                    if path_lower.endswith('.png'):
                        response_headers['Content-Type'] = 'image/png'
                    elif path_lower.endswith(('.jpg', '.jpeg')):
                        response_headers['Content-Type'] = 'image/jpeg'
                    elif path_lower.endswith('.gif'):
                        response_headers['Content-Type'] = 'image/gif'
                    elif path_lower.endswith('.svg'):
                        response_headers['Content-Type'] = 'image/svg+xml'
                    elif path_lower.endswith('.ico'):
                        response_headers['Content-Type'] = 'image/x-icon'
                    elif path_lower.endswith('.webp'):
                        response_headers['Content-Type'] = 'image/webp'
        
        # Se for HTML, ajustar URLs relativas para usar o proxy
        content_type = response_headers.get('Content-Type', '').lower()
        if 'text/html' in content_type:
            try:
                # Ler conteúdo e ajustar URLs
                content = response.content.decode('utf-8', errors='ignore')
                
                # Substituir URLs absolutas da aplicação original por URLs do proxy
                target_base = target_url.rstrip('/')
                proxy_base = f'/proxy/{app_key}'
                
                # Para buffer-forno, o base path é /buffer, então precisamos ajustar
                if app_key == 'buffer-forno':
                    buffer_base_path = '/buffer'
                else:
                    buffer_base_path = None
                
                # Ajustar URLs de recursos (CSS, JS, imagens, etc.)
                import re
                
                # 0. Para buffer-forno, PRIMEIRO capturar recursos estáticos na raiz (como /styles.css, /background2.png)
                # Isso deve ser feito ANTES de outras substituições para garantir que seja capturado
                if app_key == 'buffer-forno':
                    static_extensions = ['.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.webp', '.woff', '.woff2', '.ttf', '.eot']
                    # Padrão para capturar qualquer arquivo que comece com / e termine com extensão estática
                    # Exemplos: /styles.css, /background2.png, /script.js
                    ext_pattern = '|'.join([re.escape(ext) for ext in static_extensions])
                    
                    # Capturar em atributos: href="/styles.css", src="/background2.png"
                    pattern = rf'(href|src|action|data-src|data-href|data-url|data-action|background|background-image)\s*=\s*(["\']?)(/[^"\'>\s]*\.(?:{ext_pattern}))(["\']?)'
                    def replace_static_attr(match):
                        attr = match.group(1)
                        quote = match.group(2)
                        url = match.group(3)
                        end_quote = match.group(4)
                        if (not url.startswith(proxy_base) and 
                            not url.startswith('/buffer') and 
                            not url.startswith('/login') and 
                            not url.startswith('/logout') and 
                            not url.startswith('/static/')):
                            return f'{attr}={quote}{proxy_base}/buffer{url}{end_quote}'
                        return match.group(0)
                    
                    content = re.sub(
                        pattern,
                        replace_static_attr,
                        content,
                        flags=re.IGNORECASE
                    )
                    
                    # Capturar também em tags: <link href="/styles.css">, <img src="/background2.png">
                    pattern_tag = rf'(<link[^>]*href\s*=\s*["\']?)(/[^"\'>\s]*\.(?:{ext_pattern}))(["\']?[^>]*>)'
                    def replace_static_tag(match):
                        start = match.group(1)
                        url = match.group(2)
                        end = match.group(3)
                        if not url.startswith(proxy_base) and not url.startswith('/buffer'):
                            return f'{start}{proxy_base}/buffer{url}{end}'
                        return match.group(0)
                    
                    content = re.sub(
                        pattern_tag,
                        replace_static_tag,
                        content,
                        flags=re.IGNORECASE
                    )
                    
                    pattern_img = rf'(<img[^>]*src\s*=\s*["\']?)(/[^"\'>\s]*\.(?:{ext_pattern}))(["\']?[^>]*>)'
                    content = re.sub(
                        pattern_img,
                        replace_static_tag,
                        content,
                        flags=re.IGNORECASE
                    )
                
                # 1. URLs absolutas que apontam para a aplicação original
                content = re.sub(
                    rf'{re.escape(target_base)}(/[^"\'>\s]*)',
                    rf'{proxy_base}\1',
                    content,
                    flags=re.IGNORECASE
                )
                
                # 1.1. Para buffer-forno, também substituir URLs que começam com /buffer
                if app_key == 'buffer-forno':
                    # Substituir /buffer/... por /proxy/buffer-forno/buffer/...
                    content = re.sub(
                        r'(href|src|action|data-src|data-href|data-url|data-action|background|background-image)\s*=\s*(["\']?)(/buffer/[^"\'>\s]*)(["\']?)',
                        lambda m: f'{m.group(1)}={m.group(2)}{proxy_base}{m.group(3)[6:]}{m.group(4)}' if not m.group(3).startswith(proxy_base) else m.group(0),
                        content,
                        flags=re.IGNORECASE
                    )
                    # Substituir /buffer (sem barra final) também
                    content = re.sub(
                        r'(href|src|action|data-src|data-href|data-url|data-action|background|background-image)\s*=\s*(["\']?)(/buffer)(["\']?)',
                        lambda m: f'{m.group(1)}={m.group(2)}{proxy_base}/buffer{m.group(4)}' if not m.group(3).startswith(proxy_base) else m.group(0),
                        content,
                        flags=re.IGNORECASE
                    )
                
                # 1.5. Capturar URLs que começam com /assets/, /static/, /css/, /js/, /images/, etc.
                # Essas são comuns em aplicações web e precisam ser proxyadas
                common_paths = ['/assets/', '/static/', '/css/', '/js/', '/images/', '/img/', '/fonts/', '/vendor/']
                for common_path in common_paths:
                    # Substituir em atributos href e src
                    pattern = rf'((?:href|src|action)\s*=\s*["\']?)({re.escape(common_path)}[^"\'>\s]*)'
                    content = re.sub(
                        pattern,
                        lambda m: f'{m.group(1)}{proxy_base}{m.group(2)}' if not m.group(2).startswith(proxy_base) else m.group(0),
                        content,
                        flags=re.IGNORECASE
                    )
                
                # 1.6. Para buffer-forno, capturar recursos estáticos que começam com / (como /styles.css, /background2.png)
                # Estes recursos estão na raiz da aplicação /buffer, então precisam ser proxyados como /proxy/buffer-forno/buffer/...
                if app_key == 'buffer-forno':
                    static_extensions = ['.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.webp', '.woff', '.woff2', '.ttf', '.eot']
                    
                    # Função para substituir recursos estáticos na raiz
                    def replace_buffer_static(match):
                        attr = match.group(1)
                        quote = match.group(2) if match.lastindex >= 2 else '"'
                        url = match.group(3) if match.lastindex >= 3 else match.group(2)
                        end_quote = match.group(4) if match.lastindex >= 4 else quote
                        
                        # Não substituir se já estiver no proxy ou for URL absoluta
                        if url.startswith(proxy_base) or url.startswith('http://') or url.startswith('https://') or url.startswith('//'):
                            return match.group(0)
                        # Não substituir URLs do Maestro
                        if url.startswith('/login') or url.startswith('/logout') or url.startswith('/static/'):
                            return match.group(0)
                        # Não substituir se já começar com /buffer (já está correto)
                        if url.startswith('/buffer'):
                            return match.group(0)
                        # Substituir recursos estáticos que começam com / e têm extensão
                        if url.startswith('/') and any(url.lower().endswith(ext) for ext in static_extensions):
                            return f'{attr}={quote}{proxy_base}/buffer{url}{end_quote}'
                        return match.group(0)
                    
                    # Aplicar substituição para recursos estáticos em atributos HTML
                    # Padrão mais específico para capturar /arquivo.ext
                    content = re.sub(
                        r'(href|src|action|data-src|data-href|data-url|data-action|background|background-image)\s*=\s*(["\']?)(/[^"\'>\s]*\.(?:css|js|png|jpg|jpeg|gif|svg|ico|webp|woff|woff2|ttf|eot))(["\']?)',
                        replace_buffer_static,
                        content,
                        flags=re.IGNORECASE
                    )
                    
                    # Também capturar URLs que começam diretamente com / e têm extensão (sem atributo explícito)
                    # Isso pode acontecer em alguns contextos
                    content = re.sub(
                        r'(["\'])(/[^"\']*\.(?:css|js|png|jpg|jpeg|gif|svg|ico|webp|woff|woff2|ttf|eot))(["\'])',
                        lambda m: f'{m.group(1)}{proxy_base}/buffer{m.group(2)}{m.group(3)}' if not m.group(2).startswith(proxy_base) and not m.group(2).startswith('/buffer') and not m.group(2).startswith('/login') and not m.group(2).startswith('/logout') and not m.group(2).startswith('/static/') else m.group(0),
                        content,
                        flags=re.IGNORECASE
                    )
                
                # 2. URLs relativas em atributos HTML (href, src, action, url, data-src, etc.)
                # Melhorar regex para capturar mais padrões, incluindo URLs sem aspas
                def replace_html_url(match):
                    attr = match.group(1)
                    quote = match.group(2) if match.lastindex >= 2 else '"'
                    url = match.group(3) if match.lastindex >= 3 else match.group(2)
                    end_quote = match.group(4) if match.lastindex >= 4 else quote
                    # Não substituir se já estiver no proxy ou for URL absoluta
                    if url.startswith(proxy_base) or url.startswith('http://') or url.startswith('https://') or url.startswith('//'):
                        return match.group(0)
                    # Não substituir URLs do Maestro
                    if url.startswith('/login') or url.startswith('/logout') or url.startswith('/static/'):
                        return match.group(0)
                    # Para buffer-forno, não substituir se já começar com /buffer
                    if app_key == 'buffer-forno' and url.startswith('/buffer'):
                        return match.group(0)
                    # Substituir URLs relativas
                    if url.startswith('/'):
                        # Para buffer-forno, adicionar /buffer antes da URL
                        if app_key == 'buffer-forno':
                            return f'{attr}={quote}{proxy_base}/buffer{url}{end_quote}'
                        else:
                            return f'{attr}={quote}{proxy_base}{url}{end_quote}'
                    return match.group(0)
                
                # Padrão mais abrangente para atributos HTML
                content = re.sub(
                    r'(href|src|action|data-src|data-href|data-url|data-action|background|background-image)\s*=\s*(["\']?)(/[^"\'>\s]*)(["\']?)',
                    replace_html_url,
                    content,
                    flags=re.IGNORECASE
                )
                
                # Também capturar URLs em atributos sem aspas (menos comum mas possível)
                content = re.sub(
                    r'(href|src|action)\s*=\s*([^"\'>\s/]+)(/[^"\'>\s]*)',
                    lambda m: f'{m.group(1)}="{proxy_base}{m.group(3)}"' if m.group(3).startswith('/') and not m.group(3).startswith(proxy_base) else m.group(0),
                    content,
                    flags=re.IGNORECASE
                )
                
                # 2.5. Substituição específica para tags <link> (CSS) - importante para recursos estáticos
                # Capturar <link rel="stylesheet" href="/assets/...">
                def replace_link_tag(match):
                    href = match.group(2)
                    if href.startswith(proxy_base) or href.startswith('/static/'):
                        return match.group(0)
                    # Para buffer-forno, recursos que começam com / e não são /buffer precisam de /buffer antes
                    if app_key == 'buffer-forno' and href.startswith('/') and not href.startswith('/buffer'):
                        # Verificar se é um recurso estático (tem extensão)
                        static_exts = ['.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.webp']
                        if any(href.lower().endswith(ext) for ext in static_exts):
                            return f'{match.group(1)}{proxy_base}/buffer{href}{match.group(3)}'
                        # Se não for recurso estático conhecido, também adicionar /buffer
                        return f'{match.group(1)}{proxy_base}/buffer{href}{match.group(3)}'
                    elif href.startswith('/'):
                        return f'{match.group(1)}{proxy_base}{href}{match.group(3)}'
                    return match.group(0)
                
                content = re.sub(
                    r'(<link[^>]*href\s*=\s*["\']?)(/[^"\'>\s]+)(["\']?[^>]*>)',
                    replace_link_tag,
                    content,
                    flags=re.IGNORECASE
                )
                
                # 2.6. Substituição específica para tags <script> (JavaScript)
                # Capturar <script src="/js/...">
                def replace_script_tag(match):
                    src = match.group(2)
                    if src.startswith(proxy_base) or src.startswith('/static/'):
                        return match.group(0)
                    if app_key == 'buffer-forno' and src.startswith('/') and not src.startswith('/buffer'):
                        return f'{match.group(1)}{proxy_base}/buffer{src}{match.group(3)}'
                    elif src.startswith('/'):
                        return f'{match.group(1)}{proxy_base}{src}{match.group(3)}'
                    return match.group(0)
                
                content = re.sub(
                    r'(<script[^>]*src\s*=\s*["\']?)(/[^"\'>\s]+)(["\']?[^>]*>)',
                    replace_script_tag,
                    content,
                    flags=re.IGNORECASE
                )
                
                # 2.7. Substituição específica para tags <img> (imagens)
                # Capturar <img src="/images/...">
                def replace_img_tag(match):
                    src = match.group(2)
                    if src.startswith(proxy_base) or src.startswith('/static/'):
                        return match.group(0)
                    # Para buffer-forno, recursos que começam com / e não são /buffer precisam de /buffer antes
                    if app_key == 'buffer-forno' and src.startswith('/') and not src.startswith('/buffer'):
                        # Verificar se é um recurso estático (tem extensão de imagem)
                        img_exts = ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.webp']
                        if any(src.lower().endswith(ext) for ext in img_exts):
                            return f'{match.group(1)}{proxy_base}/buffer{src}{match.group(3)}'
                        # Se não for recurso estático conhecido, também adicionar /buffer
                        return f'{match.group(1)}{proxy_base}/buffer{src}{match.group(3)}'
                    elif src.startswith('/'):
                        return f'{match.group(1)}{proxy_base}{src}{match.group(3)}'
                    return match.group(0)
                
                content = re.sub(
                    r'(<img[^>]*src\s*=\s*["\']?)(/[^"\'>\s]+)(["\']?[^>]*>)',
                    replace_img_tag,
                    content,
                    flags=re.IGNORECASE
                )
                
                # 3. URLs em CSS inline (url(...))
                def replace_css_url(match):
                    url_path = match.group(1)
                    if url_path.startswith(proxy_base) or url_path.startswith('/static/'):
                        return match.group(0)
                    if app_key == 'buffer-forno' and url_path.startswith('/') and not url_path.startswith('/buffer'):
                        return f'url("{proxy_base}/buffer{url_path}")'
                    elif url_path.startswith('/'):
                        return f'url("{proxy_base}{url_path}")'
                    return match.group(0)
                
                content = re.sub(
                    r'url\s*\(\s*["\']?(/[^"\')\s]*)["\']?\s*\)',
                    replace_css_url,
                    content,
                    flags=re.IGNORECASE
                )
                
                # 4. URLs em JavaScript inline (mais específico para evitar falsos positivos)
                # Captura apenas strings que parecem URLs (contêm / e não são comentários)
                # IMPORTANTE: Não modificar regex patterns dentro de scripts para evitar erros
                def replace_js_urls(match):
                    quote = match.group(1)
                    url = match.group(2)
                    end_quote = match.group(3)
                    
                    # Não modificar se parecer ser parte de uma regex (contém padrões de regex)
                    # Verificar padrões comuns de regex que não são URLs
                    regex_patterns = [
                        r'^\*',  # Começa com *
                        r'\+\s*$',  # Termina com +
                        r'\?\s*$',  # Termina com ?
                        r'^\[',  # Começa com [
                        r'^\{',  # Começa com {
                        r'\|\|',  # Contém ||
                        r'\^\s*$',  # Termina com ^
                        r'\$\s*$',  # Termina com $
                    ]
                    if any(re.search(pattern, url) for pattern in regex_patterns):
                        return match.group(0)
                    
                    # Se contém caracteres de regex mas parece ser uma URL (tem extensão de arquivo)
                    if any(char in url for char in ['*', '+', '?', '(', ')', '[', ']', '{', '}', '|', '^', '$']):
                        # Se não parece ser uma URL (não tem extensão de arquivo comum), provavelmente é regex
                        if not any(url.lower().endswith(ext) for ext in ['.js', '.css', '.html', '.json', '.xml', '.png', '.jpg', '.gif', '.svg', '.ico']):
                            # Mas ainda pode ser uma URL se começa com / e tem / no meio
                            if not (url.startswith('/') and '/' in url[1:]):
                                return match.group(0)
                    
                    # Só substituir se parecer uma URL (começa com / e não é // ou já está no proxy)
                    # Ser mais conservador para evitar modificar regex patterns
                    if (url.startswith('/') and 
                        not url.startswith('//') and 
                        not url.startswith(proxy_base) and
                        not url.startswith('/login') and
                        not url.startswith('/logout')):
                        # Verificar se é realmente uma URL (tem extensão de arquivo ou parece ser um path)
                        is_url = (
                            any(url.lower().endswith(ext) for ext in ['.js', '.css', '.html', '.json', '.xml', '.png', '.jpg', '.gif', '.svg', '.ico']) or
                            ('/' in url and url.count('/') >= 1) or
                            url.endswith('/')
                        )
                        if is_url:
                            # Para buffer-forno, adicionar /buffer antes da URL
                            if app_key == 'buffer-forno' and not url.startswith('/buffer'):
                                return f'{quote}{proxy_base}/buffer{url}{end_quote}'
                            else:
                                return f'{quote}{proxy_base}{url}{end_quote}'
                    return match.group(0)
                
                # Aplicar apenas em contextos JavaScript (dentro de <script> tags)
                # Mas pular scripts que são type="text/template" ou similares
                script_pattern = r'(<script[^>]*>)(.*?)(</script>)'
                def process_script(match):
                    script_start = match.group(1)
                    script_content = match.group(2)
                    script_end = match.group(3)
                    
                    # Pular se for template ou tipo especial
                    if 'type=' in script_start.lower() and any(t in script_start.lower() for t in ['template', 'text/template', 'text/x-handlebars']):
                        return match.group(0)
                    
                    # Para buffer-forno, ser mais agressivo na substituição de URLs
                    # Mas ainda evitar modificar regex patterns
                    if app_key == 'buffer-forno':
                        # Substituir URLs que claramente são recursos (têm extensão de arquivo)
                        def replace_buffer_js_url(m):
                            quote = m.group(1)
                            url = m.group(2)
                            end_quote = m.group(3)
                            
                            # Verificar se é realmente uma URL de recurso (tem extensão)
                            static_exts = ['.js', '.css', '.html', '.json', '.xml', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico']
                            if (url.startswith('/') and 
                                not url.startswith('//') and 
                                not url.startswith(proxy_base) and
                                not url.startswith('/buffer') and
                                any(url.lower().endswith(ext) for ext in static_exts)):
                                return f'{quote}{proxy_base}/buffer{url}{end_quote}'
                            return m.group(0)
                        
                        script_content = re.sub(
                            r'(["\'])(/[^"\']*\.(?:js|css|html|json|xml|png|jpg|jpeg|gif|svg|ico))(["\'])',
                            replace_buffer_js_url,
                            script_content,
                            flags=re.IGNORECASE
                        )
                    else:
                        # Para outras aplicações, usar lógica mais conservadora
                        script_content = re.sub(
                            r'(["\'])(/[^"\']*)(["\'])',
                            replace_js_urls,
                            script_content,
                            flags=re.IGNORECASE
                        )
                    return f'{script_start}{script_content}{script_end}'
                
                content = re.sub(
                    script_pattern,
                    process_script,
                    content,
                    flags=re.IGNORECASE | re.DOTALL
                )
                
                # 5. Remover CSP do HTML proxyado se existir (para não conflitar)
                content = re.sub(
                    r'<meta[^>]*http-equiv=["\']Content-Security-Policy["\'][^>]*>',
                    '',
                    content,
                    flags=re.IGNORECASE
                )
                
                # Sanitizar HTML antes de injetar script
                # (o script é seguro, mas vamos garantir)
                proxy_base_safe = proxy_base.replace("'", "\\'").replace('"', '\\"')
                
                # CSS para o botão Home (estilo futurista)
                home_button_css = """
<style id="maestro-home-button-style">
.maestro-home-button {
    position: fixed;
    top: 20px;
    left: 50%;
    transform: translateX(-50%);
    z-index: 999999;
    background: rgba(0, 0, 0, 0.85);
    backdrop-filter: blur(20px) saturate(180%);
    -webkit-backdrop-filter: blur(20px) saturate(180%);
    border: 1px solid rgba(0, 212, 255, 0.5);
    border-radius: 12px;
    padding: 12px 20px;
    text-decoration: none;
    color: #00d4ff;
    font-family: 'Orbitron', 'Rajdhani', -apple-system, BlinkMacSystemFont, sans-serif;
    font-weight: 600;
    font-size: 14px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    display: flex;
    align-items: center;
    gap: 8px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 4px 16px rgba(0, 212, 255, 0.3), 
                0 0 20px rgba(0, 212, 255, 0.2),
                inset 0 0 20px rgba(0, 212, 255, 0.1);
    cursor: pointer;
    user-select: none;
    -webkit-user-select: none;
    opacity: 0.9;
}

.maestro-home-button:hover {
    opacity: 1;
    transform: translateX(-50%) translateY(-2px) scale(1.05);
    border-color: #00ffff;
    box-shadow: 0 8px 32px rgba(0, 212, 255, 0.5), 
                0 0 40px rgba(0, 212, 255, 0.4),
                inset 0 0 30px rgba(0, 212, 255, 0.2);
    color: #00ffff;
}

.maestro-home-button:active {
    transform: translateX(-50%) translateY(0) scale(0.98);
}

.maestro-home-button-icon {
    font-size: 18px;
    line-height: 1;
    filter: drop-shadow(0 0 8px currentColor);
    transition: transform 0.3s ease;
}

.maestro-home-button:hover .maestro-home-button-icon {
    transform: scale(1.2) rotate(-10deg);
}

.maestro-home-button-text {
    position: relative;
}

.maestro-home-button::before {
    content: '';
    position: absolute;
    top: -2px;
    left: -2px;
    right: -2px;
    bottom: -2px;
    background: linear-gradient(45deg, #00d4ff, #00ffff, #00d4ff);
    border-radius: 14px;
    opacity: 0;
    z-index: -1;
    filter: blur(8px);
    transition: opacity 0.3s ease;
}

.maestro-home-button:hover::before {
    opacity: 0.6;
}

/* Responsividade para mobile */
@media (max-width: 768px) {
    .maestro-home-button {
        top: 10px;
        left: 50%;
        transform: translateX(-50%);
        padding: 10px 16px;
        font-size: 12px;
        border-radius: 10px;
    }
    
    .maestro-home-button:hover {
        transform: translateX(-50%) translateY(-2px) scale(1.05);
    }
    
    .maestro-home-button:active {
        transform: translateX(-50%) translateY(0) scale(0.98);
    }
    
    .maestro-home-button-icon {
        font-size: 16px;
    }
}

@media (max-width: 480px) {
    .maestro-home-button {
        top: 8px;
        left: 50%;
        transform: translateX(-50%);
        padding: 8px 12px;
        font-size: 11px;
        gap: 6px;
    }
    
    .maestro-home-button:hover {
        transform: translateX(-50%) translateY(-2px) scale(1.05);
    }
    
    .maestro-home-button:active {
        transform: translateX(-50%) translateY(0) scale(0.98);
    }
    
    .maestro-home-button-text {
        display: none;
    }
    
    .maestro-home-button-icon {
        font-size: 18px;
    }
}
</style>
"""
                
                # HTML do botão Home
                home_button_html = """
<div id="maestro-home-button-container">
    <a href="/" class="maestro-home-button" title="Voltar para o Portal Maestro">
        <span class="maestro-home-button-icon">🏠</span>
        <span class="maestro-home-button-text">Home</span>
    </a>
</div>
"""
                
                # Injetar script para interceptar requisições de API
                proxy_script = f"""
<script>
(function() {{
    const PROXY_BASE = '{proxy_base_safe}';
    
    // Função para verificar se uma URL deve ser redirecionada para o proxy
    function shouldProxy(url) {{
        if (typeof url !== 'string') return false;
        // Não proxy URLs absolutas (http://, https://, //)
        if (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('//')) return false;
        // Não proxy URLs que já estão no proxy
        if (url.startsWith(PROXY_BASE)) return false;
        // Não proxy URLs do próprio Maestro
        if (url.startsWith('/login') || url.startsWith('/logout') || url.startsWith('/static/')) return false;
        // Proxy todas as outras URLs relativas (incluindo recursos estáticos: CSS, JS, imagens, etc.)
        return url.startsWith('/');
    }}
    
    // Interceptar também tags <link> e <img> que podem ser adicionadas dinamicamente
    const originalCreateElement = document.createElement;
    document.createElement = function(tagName, options) {{
        const element = originalCreateElement.call(this, tagName, options);
        if (tagName.toLowerCase() === 'link' || tagName.toLowerCase() === 'img' || tagName.toLowerCase() === 'script') {{
            const originalSetAttribute = element.setAttribute.bind(element);
            element.setAttribute = function(name, value) {{
                if ((name === 'href' || name === 'src') && shouldProxy(value)) {{
                    value = PROXY_BASE + value;
                }}
                return originalSetAttribute(name, value);
            }};
        }}
        return element;
    }};
    
    // Interceptar fetch()
    const originalFetch = window.fetch;
    window.fetch = function(url, options) {{
        if (shouldProxy(url)) {{
            url = PROXY_BASE + url;
        }}
        return originalFetch.call(this, url, options);
    }};
    
    // Interceptar XMLHttpRequest
    const originalOpen = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function(method, url, async, user, password) {{
        if (shouldProxy(url)) {{
            url = PROXY_BASE + url;
        }}
        return originalOpen.call(this, method, url, async, user, password);
    }};
    
    // Interceptar $.ajax do jQuery se estiver disponível
    if (window.jQuery && window.jQuery.ajaxSetup) {{
        const originalAjax = window.jQuery.ajax;
        window.jQuery.ajax = function(options) {{
            if (options && options.url && shouldProxy(options.url)) {{
                options.url = PROXY_BASE + options.url;
            }}
            return originalAjax.call(this, options);
        }};
    }}
}})();
</script>
"""
                # Injetar CSS e script no <head>
                head_injection = home_button_css + proxy_script
                
                # Injetar CSS e script antes do fechamento do </head>
                if '</head>' in content:
                    content = content.replace('</head>', head_injection + '</head>')
                elif '<body' in content:
                    # Se não tiver </head>, injetar no início do body (CSS e script funcionam no body também)
                    content = re.sub(r'(<body[^>]*>)', r'\1' + head_injection, content, flags=re.IGNORECASE)
                else:
                    # Se não tiver nem </head> nem <body>, adicionar no início
                    content = head_injection + content
                
                # Injetar HTML do botão no <body>
                if '<body' in content:
                    # Verificar se o botão já não foi inserido
                    if 'maestro-home-button-container' not in content:
                        # Inserir no início do body
                        content = re.sub(
                            r'(<body[^>]*>)',
                            r'\1' + home_button_html,
                            content,
                            flags=re.IGNORECASE
                        )
                else:
                    # Se não tiver body, adicionar o botão no final do conteúdo
                    content = content + home_button_html
                
                # Log do acesso via proxy
                log_proxy_access(app_key, path, response.status_code)
                
                return Response(
                    content,
                    status=response.status_code,
                    headers=response_headers,
                    mimetype='text/html'
                )
            except Exception as e:
                import logging
                logging.warning(f"Erro ao processar HTML do proxy: {str(e)}")
                # Se der erro, retornar conteúdo original
                return Response(
                    stream_with_context(generate()),
                    status=response.status_code,
                    headers=response_headers
                )
        else:
            # Para outros tipos de conteúdo (CSS, JS, imagens, etc.), retornar como está
            # Mas garantir que o MIME type esteja correto
            mimetype = None
            if 'Content-Type' in response_headers:
                mimetype = response_headers['Content-Type'].split(';')[0].strip()
            
            return Response(
                stream_with_context(generate()),
                status=response.status_code,
                headers=response_headers,
                mimetype=mimetype
            )
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Erro no proxy para {app_key}: {str(e)}")
        log_proxy_access(app_key, path, 500)
        flash(f'Erro ao acessar a aplicação. Tente novamente.', 'error')
        return redirect(url_for('index'))

if __name__ == '__main__':
    # Configurações para produção em Docker
    port = int(os.environ.get('PORT', 8000))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    app.run(host=host, port=port, debug=debug)
