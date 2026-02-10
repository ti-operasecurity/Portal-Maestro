from flask import Flask, render_template, request, redirect, url_for, session, flash, Response, stream_with_context
import json
import os
import requests
import hashlib
from io import BytesIO
from auth import auth_manager, login_required, admin_required, init_auth, ServiceUnavailableError
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

# Helper CORS: origem permitida (nunca * com credentials). Mantém acesso por domínio ou IP.
def _get_allowed_origin():
    """Retorna a origem permitida para CORS (mesmo host/domínio do Maestro), sem usar *."""
    origin = request.headers.get('Origin')
    host = request.headers.get('Host', '')
    allowed_hosts = ('maestro.opera.security', 'localhost', '127.0.0.1')
    def _allowed(o):
        if not o:
            return False
        try:
            p = urlparse(o)
            netloc = (p.hostname or '').lower()
            return (netloc in allowed_hosts or netloc.endswith('.opera.security') or
                    (host and netloc == host.split(':')[0].lower()))
        except Exception:
            return False
    if origin and _allowed(origin):
        return origin
    if host:
        scheme = request.headers.get('X-Forwarded-Proto', 'https' if request.is_secure else 'http')
        return f"{scheme}://{host}"
    return request.url_root.rstrip('/') or 'https://maestro.opera.security'

# Expor CSRF token nos templates
@app.context_processor
def inject_csrf():
    """Injeta função CSRF token em todos os templates"""
    from flask_wtf.csrf import generate_csrf
    return dict(csrf_token=lambda: generate_csrf())

# Filtro para formatar data e hora
@app.template_filter('format_datetime')
def format_datetime_filter(value):
    """Formata data e hora para exibição legível, convertendo de UTC para timezone local"""
    if not value:
        return 'Nunca'
    
    try:
        from datetime import datetime, timezone
        # Tentar usar zoneinfo (Python 3.9+), senão usar pytz como fallback
        try:
            from zoneinfo import ZoneInfo
        except ImportError:
            try:
                import pytz
                ZoneInfo = lambda tz: pytz.timezone(tz)
            except ImportError:
                # Se não tiver nenhum, usar UTC-3 manualmente
                ZoneInfo = None
        
        # Timezone do Brasil (America/Sao_Paulo = UTC-3)
        tz_brasil = ZoneInfo('America/Sao_Paulo') if ZoneInfo else None
        
        # Tentar diferentes formatos de data
        if isinstance(value, str):
            # Formato ISO: 2025-12-03T14:55:52+00:00 ou 2025-12-03T14:55:52 ou 2025-12-03T14:55:52Z
            if 'T' in value:
                # Tentar parsear com timezone
                if value.endswith('Z'):
                    # UTC explícito
                    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    dt = dt.replace(tzinfo=timezone.utc)
                elif '+' in value or value.count('-') > 2:
                    # Tem timezone explícito
                    dt = datetime.fromisoformat(value)
                else:
                    # Sem timezone - assumir UTC (como salvo no banco)
                    dt = datetime.strptime(value.split('.')[0], '%Y-%m-%dT%H:%M:%S')
                    dt = dt.replace(tzinfo=timezone.utc)
            else:
                # Tentar outros formatos
                dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
        elif isinstance(value, datetime):
            dt = value
            # Se não tiver timezone, assumir UTC
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        else:
            return str(value)
        
        # Converter de UTC para timezone local (America/Sao_Paulo)
        if tz_brasil:
            dt_local = dt.astimezone(tz_brasil)
        else:
            # Fallback: subtrair 3 horas manualmente (UTC-3)
            # Se dt já tem timezone, converter para naive primeiro
            if dt.tzinfo is not None:
                # Converter para UTC naive (remover timezone mas manter o horário UTC)
                dt_utc = dt.replace(tzinfo=None)
            else:
                dt_utc = dt
            # Subtrair 3 horas (UTC-3 = America/Sao_Paulo)
            dt_local = dt_utc - timedelta(hours=3)
        
        # Formatar em português de forma legível
        meses = ['', 'jan', 'fev', 'mar', 'abr', 'mai', 'jun', 
                 'jul', 'ago', 'set', 'out', 'nov', 'dez']
        
        dia = dt_local.day
        mes = meses[dt_local.month]
        ano = dt_local.year
        hora = dt_local.hour
        minuto = dt_local.minute
        
        # Formato: "03 dez 2025, 14:55"
        return f"{dia:02d} {mes} {ano}, {hora:02d}:{minuto:02d}h"
    except Exception as e:
        import logging
        logging.error(f"Erro ao formatar data: {str(e)} - Valor: {value}")
        # Se houver erro, retornar formato simplificado
        if isinstance(value, str):
            return value[:19].replace('T', ' ')
        return str(value)

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
        # CORS: mesma origem (nunca * com credentials)
        if 'Access-Control-Allow-Origin' not in response.headers:
            response.headers['Access-Control-Allow-Origin'] = _get_allowed_origin()
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
    response.headers['X-XSS-Protection'] = '1; mode=block'  # Alinhado com Nginx; evita sinalizar 0 em scanners
    
    # CORS: mesma origem (helper evita * com credentials)
    host = request.headers.get('Host', '')
    response.headers['Access-Control-Allow-Origin'] = _get_allowed_origin()
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
# Ordem: 4 cards no topo + 4 cards embaixo (todos do mesmo tamanho)
APLICACOES = [
    # Topo - 4 cards
    {
        'nome': 'Monitoração Produtiva',
        'url': 'http://10.150.16.45:8082/',
        'url_proxy': '/proxy/painel-monitoracao',  # URL através do proxy
        'icone': '📊',
        'cor': '#3b82f6',  # Azul vibrante
        'tamanho': 'pequeno'  # Card pequeno
    },
    {
        'nome': 'Dashboard de Perdas',
        'url': 'http://10.150.16.45:5253/',
        'url_proxy': '/proxy/dashboard-perdas',
        'icone': '📉',
        'cor': '#ef4444',  # Vermelho para alertas/perdas
        'tamanho': 'pequeno'  # Card pequeno
    },
    {
        'nome': 'Dashboard de Produção',
        'url': 'http://10.150.16.45:8092/',
        'url_proxy': '/proxy/dashboard-producao',
        'icone': '📈',
        'cor': '#10b981',  # Verde para produção
        'tamanho': 'pequeno'  # Card pequeno
    },
    {
        'nome': 'BUFFER do FORNO',
        'url': 'http://10.150.16.45:4300/buffer',
        'url_proxy': '/proxy/buffer-forno',
        'icone': '🔄',
        'cor': '#14b8a6',  # Teal para buffer/produção
        'tamanho': 'pequeno'  # Card pequeno
    },
    # Embaixo - 2 cards
    {
        'nome': 'Aging de Estoque',
        'url': 'http://10.150.16.45:8079/',
        'url_proxy': '/proxy/aging-estoque',
        'icone': '📦',
        'cor': '#06b6d4',  # Ciano para estoque
        'tamanho': 'pequeno'  # Card pequeno
    },
    {
        'nome': 'Dash Ocupação Forno',
        'url': 'http://10.150.16.45:5123/dashboard_ocupacao',
        'url_proxy': '/proxy/dashboard-ocupacao-forno',
        'icone': '🔥',
        'cor': '#f59e0b',  # Laranja/Amarelo para forno
        'tamanho': 'pequeno'  # Card pequeno
    },
    {
        'nome': 'Dashboard de Fluxo por Etapas',
        'url': 'http://10.150.16.45:9191/',
        'url_proxy': '/proxy/dashboard-fluxo-etapas',
        'icone': '🔀',
        'cor': '#8b5cf6',  # Roxo/Violeta para fluxo
        'tamanho': 'pequeno'  # Card pequeno
    }
]

# Mapeamento de rotas proxy para URLs reais
PROXY_ROUTES = {
    'painel-monitoracao': 'http://10.150.16.45:8082',
    'dashboard-perdas': 'http://10.150.16.45:5253',
    'dashboard-producao': 'http://10.150.16.45:8092',
    'monitoramento-fornos': 'http://10.150.16.45:8081',
    'robo-logistica': 'http://10.150.16.45:8088',
    'monitoramento-autoclaves': 'http://10.150.16.45:8080',
    'aging-estoque': 'http://10.150.16.45:8079',
    'buffer-forno': 'http://10.150.16.45:4300',
    # Aba Aplicações (portal) - manter alias antigo para compatibilidade
    'app-8090': 'http://10.150.16.45:8090',
    'Vinculação de ProductionOrders-SAP': 'http://10.150.16.45:8090',  # Alias antigo (compatibilidade)
    'Orquestrador de Ordens de Produção-SAP': 'http://10.150.16.45:8090',  # Novo nome
    # HTTPS para a aplicação com certificado próprio
    'gestao-estoque-sap': 'https://10.150.16.45:8091',
    # Apontamento Forno
    'apontamento-forno': 'http://10.150.16.45:4000/apontamento_forno',
    # Apontamento Inspeção Final
    'apontamento-inspecao-final': 'https://10.150.16.45:9010',
    # Etiquetas Montagem
    'etiquetas-montagem': 'https://10.150.16.45:9022',
    # Dashboard Ocupação Forno
    'dashboard-ocupacao-forno': 'http://10.150.16.45:5123',
    # Dashboard Ocupação Hoje (Forno)
    'dashboard-ocupacao-hoje': 'http://10.150.16.45:5123',
    # Dashboard de Fluxo por Etapas
    'dashboard-fluxo-etapas': 'http://10.150.16.45:9191',
    # Portal de Procedimentos
    'portal-procedimentos': 'http://10.150.16.45:9110',
    # Aba Dashboards: Inspeção Final x Estoque
    'inspecao-final-estoque': 'http://10.150.16.45:8093'
}

# Verificação de certificado por app (True = verificar, False = aceitar self-signed)
PROXY_VERIFY = {
    'gestao-estoque-sap': False,
    'apontamento-inspecao-final': False,  # HTTPS com certificado próprio (possivelmente self-signed)
    'etiquetas-montagem': False  # HTTPS com certificado próprio (possivelmente self-signed)
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
        response.headers['Access-Control-Allow-Origin'] = _get_allowed_origin()
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

# ============================================
# ROTAS DE ADMINISTRAÇÃO
# ============================================

@app.route('/admin/users')
@admin_required
def admin_users():
    """Lista usuários com busca e paginação (20 por página)"""
    from math import ceil
    search = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    if page < 1:
        page = 1
    per_page = 20
    users, total = auth_manager.get_users_paginated(search_term=search or None, page=page, per_page=per_page)
    total_pages = ceil(total / per_page) if total else 1
    if page > total_pages and total_pages > 0:
        page = total_pages
        users, total = auth_manager.get_users_paginated(search_term=search or None, page=page, per_page=per_page)
    groups = auth_manager.get_all_groups()
    return render_template(
        'admin/users.html',
        users=users,
        groups=groups,
        auth_manager=auth_manager,
        search=search,
        page=page,
        total_pages=total_pages,
        total=total,
        per_page=per_page
    )

@app.route('/admin/users/create', methods=['GET', 'POST'])
@admin_required
@rate_limit_api()
def admin_create_user():
    """Criar novo usuário"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        email = request.form.get('email', '').strip() or None
        group_id = request.form.get('group_id')
        
        # Validação
        username_valid, username_error = validate_username(username)
        if not username_valid:
            flash(f'Erro: {username_error}', 'error')
            groups = auth_manager.get_all_groups()
            return render_template('admin/create_user.html', groups=groups)
        
        password_valid, password_error = validate_password(password)
        if not password_valid:
            flash(f'Erro: {password_error}', 'error')
            groups = auth_manager.get_all_groups()
            return render_template('admin/create_user.html', groups=groups)
        
        # Criar usuário
        result = auth_manager.create_user(username, password, email)
        if result['success']:
            # Atribuir grupo se fornecido
            if group_id and group_id.isdigit():
                auth_manager.update_user_group(result['user_id'], int(group_id))
            flash('Usuário criado com sucesso!', 'success')
            return redirect(url_for('admin_users'))
        else:
            flash(f'Erro ao criar usuário: {result["message"]}', 'error')
    
    groups = auth_manager.get_all_groups()
    return render_template('admin/create_user.html', groups=groups)

@app.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
@rate_limit_api()
def admin_edit_user(user_id):
    """Editar usuário"""
    user = auth_manager.get_user_by_id(user_id)
    if not user:
        flash('Usuário não encontrado.', 'error')
        return redirect(url_for('admin_users'))

    # Dados auxiliares para nova aba "Aplicações"
    portal_apps = auth_manager.get_portal_apps(active_only=True)
    user_portal_app_ids = [app.get('id') for app in auth_manager.get_user_portal_apps(user_id)]
    user_portal_tab_access = True if auth_manager.is_admin(user_id) else bool(user.get('portal_tab_access'))
    
    if request.method == 'POST':
        # Atualizar informações básicas
        email = request.form.get('email', '').strip() or None
        # Checkbox: pode vir como '1' (marcado) ou '0' (desmarcado via hidden)
        # Se vier como lista (quando há checkbox e hidden), pegar o último valor
        active_value = request.form.get('active')
        
        # Tratar caso seja lista (quando há checkbox e hidden com mesmo nome)
        if isinstance(active_value, list):
            # Se for lista, pegar o último valor (o checkbox tem precedência se ambos existirem)
            # Mas se o checkbox estiver desabilitado, só terá o hidden
            active_value = active_value[-1] if active_value else '0'
        
        # Converter para string para comparação
        active_value = str(active_value) if active_value is not None else '0'
        
        if active_value == '1':
            active = True
        elif active_value == '0':
            active = False
        else:
            # Se não foi enviado ou valor inválido, manter o valor atual do usuário
            active = user.get('active', True)
            logging.warning(f"Valor de 'active' não reconhecido: {active_value}, mantendo valor atual: {active}")
        
        group_id = request.form.get('group_id', '').strip()
        new_password = request.form.get('new_password', '').strip()
        # portal_tab_access pode vir como lista (hidden 0 + checkbox 1); pegar o último valor
        portal_tab_access_list = request.form.getlist('portal_tab_access')
        portal_tab_access_value = portal_tab_access_list[-1] if portal_tab_access_list else '0'
        portal_selected_apps = request.form.getlist('portal_apps')
        
        import logging
        logging.info(f"=== ATUALIZANDO USUÁRIO {user_id} ===")
        logging.info(f"Email: {email}")
        logging.info(f"Active (valor bruto): {request.form.get('active')}")
        logging.info(f"Active (processado): {active_value} -> {active}")
        logging.info(f"Group ID: {group_id}")
        logging.info(f"Tem senha nova: {bool(new_password)}")
        logging.info(f"Aplicações no formulário: {request.form.getlist('applications')}")
        logging.info(f"Aba Aplicações (flag): {portal_tab_access_value}")
        logging.info(f"Aba Aplicações (selecionadas): {portal_selected_apps}")
        logging.info(f"Todos os dados do form: {dict(request.form)}")
        logging.info(f"================================")
        
        # Validar senha primeiro se fornecida
        if new_password:
            password_valid, password_error = validate_password(new_password)
            if not password_valid:
                flash(f'Erro na senha: {password_error}', 'error')
                groups = auth_manager.get_all_groups()
                applications = auth_manager.get_all_applications()
                user_apps = auth_manager.get_user_applications(user_id)
                user_app_ids = []
                for app in user_apps:
                    if isinstance(app, dict) and 'id' in app:
                        user_app_ids.append(app['id'])
                    elif hasattr(app, 'id'):
                        user_app_ids.append(app.id)
                # Recarregar usuário atualizado
                user = auth_manager.get_user_by_id(user_id)
                return render_template('admin/edit_user.html',
                                       user=user,
                                       groups=groups,
                                       applications=applications,
                                       user_app_ids=user_app_ids,
                                       portal_apps=portal_apps,
                                       user_portal_app_ids=user_portal_app_ids,
                                       portal_tab_access=user_portal_tab_access)
        
        try:
            # Atualizar informações básicas
            update_data = {
                'email': email,
                'active': bool(active)  # Garantir que seja boolean
            }
            
            # Adicionar group_id se fornecido
            if group_id and group_id.isdigit():
                update_data['group_id'] = int(group_id)
            elif group_id == '':
                # Se group_id for vazio, remover grupo (definir como None)
                update_data['group_id'] = None
            
            logging.info(f"Dados para atualização: {update_data}")
            
            # Atualizar dados básicos
            result = auth_manager.supabase.table('maestro_users').update(update_data).eq('id', user_id).execute()
            logging.info(f"Resultado da atualização: {result.data}")
            
            # Verificar se a atualização foi bem-sucedida
            if not result.data:
                logging.warning(f"Nenhum dado retornado da atualização para usuário {user_id}")
                flash('Aviso: A atualização pode não ter sido aplicada. Verifique os logs.', 'warning')
            else:
                logging.info(f"Usuário {user_id} atualizado com sucesso: {result.data}")
            
            # Atualizar senha se fornecida e válida
            if new_password:
                hashed_password = auth_manager.hash_password(new_password)
                password_result = auth_manager.supabase.table('maestro_users').update({
                    'password_hash': hashed_password
                }).eq('id', user_id).execute()
                
                if password_result.data:
                    flash('Usuário e senha atualizados com sucesso!', 'success')
                else:
                    flash('Usuário atualizado, mas houve um problema ao atualizar a senha.', 'warning')
            else:
                flash('Usuário atualizado com sucesso!', 'success')
            
            # Atualizar aplicações se o grupo selecionado for "Operação"
            # Verificar o grupo que foi selecionado no formulário, não o grupo atual do usuário
            selected_group_id = None
            if group_id and group_id.isdigit():
                selected_group_id = int(group_id)
            
            # Buscar informações do grupo selecionado
            selected_group = None
            if selected_group_id:
                groups_list = auth_manager.get_all_groups()
                selected_group = next((g for g in groups_list if g.get('id') == selected_group_id), None)
            
            # Se o grupo selecionado for "Operação", processar aplicações
            if selected_group and selected_group.get('name') == 'operacao':
                selected_apps = request.form.getlist('applications')
                logging.info(f"Grupo selecionado: Operação (ID: {selected_group_id}) - Atualizando aplicações para usuário {user_id}")
                logging.info(f"Aplicações selecionadas no formulário (raw): {selected_apps}")
                logging.info(f"Tipo de selected_apps: {type(selected_apps)}")
                logging.info(f"Quantidade de aplicações: {len(selected_apps)}")
                
                # Se não houver aplicações selecionadas, pode ser que não foram enviadas
                if not selected_apps:
                    logging.warning(f"⚠️ NENHUMA APLICAÇÃO FOI ENVIADA NO FORMULÁRIO!")
                    logging.warning(f"Todos os campos do form: {list(request.form.keys())}")
                    # Verificar se há algum problema com os nomes dos campos
                    all_form_data = dict(request.form)
                    logging.warning(f"Dados completos do form: {all_form_data}")
                
                try:
                    # Obter aplicações atuais do usuário
                    current_apps = auth_manager.get_user_applications(user_id)
                    current_app_ids = set()
                    for app in current_apps:
                        if isinstance(app, dict) and 'id' in app:
                            current_app_ids.add(app['id'])
                        elif hasattr(app, 'id'):
                            current_app_ids.add(app.id)
                    
                    logging.info(f"Aplicações atuais do usuário: {current_app_ids}")
                    
                    # Converter para inteiros
                    selected_app_ids = {int(app_id) for app_id in selected_apps if app_id.isdigit()}
                    logging.info(f"Aplicações selecionadas (IDs): {selected_app_ids}")
                    
                    # Remover aplicações que não estão mais selecionadas
                    apps_to_remove = current_app_ids - selected_app_ids
                    logging.info(f"Aplicações para remover: {apps_to_remove}")
                    for app_id in apps_to_remove:
                        auth_manager.revoke_application_access(user_id, app_id)
                    
                    # Adicionar novas aplicações
                    apps_to_add = selected_app_ids - current_app_ids
                    logging.info(f"Aplicações para adicionar: {apps_to_add}")
                    for app_id in apps_to_add:
                        auth_manager.grant_application_access(user_id, app_id, session.get('user_id'))
                    
                    if selected_app_ids:
                        flash('Usuário e aplicações atualizados com sucesso!', 'success')
                    else:
                        flash('Usuário atualizado. Nenhuma aplicação foi selecionada para o grupo Operação.', 'warning')
                except Exception as e:
                    import traceback
                    logging.error(f"Erro ao atualizar aplicações: {str(e)}")
                    logging.error(traceback.format_exc())
                    flash(f'Usuário atualizado, mas houve um problema ao atualizar aplicações: {str(e)}', 'warning')
            elif selected_group and selected_group.get('name') != 'operacao':
                # Se mudou de Operação para outro grupo, remover todas as aplicações
                current_apps = auth_manager.get_user_applications(user_id)
                if current_apps:
                    logging.info(f"Usuário mudou de Operação para {selected_group.get('name')} - Removendo aplicações específicas")
                    for app in current_apps:
                        app_id = app.get('id') if isinstance(app, dict) else (app.id if hasattr(app, 'id') else None)
                        if app_id:
                            auth_manager.revoke_application_access(user_id, app_id)

            # Processar flag e permissões da nova aba "Aplicações"
            try:
                is_admin_user = auth_manager.is_admin(user_id)
                is_full_user = auth_manager.is_maestro_full(user_id)
                # Apenas administrador tem acesso fixo; maestro_full pode ter a permissão desmarcada
                portal_tab_access = True if is_admin_user else (portal_tab_access_value == '1')

                auth_manager.update_portal_tab_access(user_id, portal_tab_access)

                if portal_tab_access and not is_admin_user:
                    portal_ids = []
                    for app_id in portal_selected_apps:
                        try:
                            portal_ids.append(int(app_id))
                        except ValueError:
                            continue
                    auth_manager.set_user_portal_apps(user_id, portal_ids, granted_by=session.get('user_id'))
                else:
                    # Apenas Admin tem acesso total sem lista; demais (incl. maestro_full desmarcado), limpar específicos
                    auth_manager.set_user_portal_apps(user_id, [], granted_by=session.get('user_id'))
            except Exception as e:
                import traceback
                logging.error(f"Erro ao processar aba Aplicações (nova): {str(e)}")
                logging.error(traceback.format_exc())
                flash('Usuário atualizado, mas houve erro ao salvar permissões da aba Aplicações.', 'warning')
            
            # Sempre redirecionar, mesmo se houver avisos
            return redirect(url_for('admin_users'))
        except Exception as e:
            import logging
            import traceback
            error_msg = f"Erro ao atualizar usuário {user_id}: {str(e)}"
            logging.error(error_msg)
            logging.error(traceback.format_exc())
            flash(f'Erro ao atualizar usuário: {str(e)}', 'error')
            
            # Retornar para a página de edição com erro
            groups = auth_manager.get_all_groups()
            applications = auth_manager.get_all_applications()
            user_apps = auth_manager.get_user_applications(user_id)
            user_app_ids = []
            for app in user_apps:
                if isinstance(app, dict) and 'id' in app:
                    user_app_ids.append(app['id'])
                elif hasattr(app, 'id'):
                    user_app_ids.append(app.id)
            user = auth_manager.get_user_by_id(user_id)
            return render_template('admin/edit_user.html',
                                   user=user,
                                   groups=groups,
                                   applications=applications,
                                   user_app_ids=user_app_ids,
                                   portal_apps=portal_apps,
                                   user_portal_app_ids=user_portal_app_ids,
                                   portal_tab_access=user_portal_tab_access)
    
    groups = auth_manager.get_all_groups()
    applications = auth_manager.get_all_applications()
    user_apps = auth_manager.get_user_applications(user_id)
    # Garantir que extraímos os IDs corretamente
    user_app_ids = []
    for app in user_apps:
        if isinstance(app, dict) and 'id' in app:
            user_app_ids.append(app['id'])
        elif hasattr(app, 'id'):
            user_app_ids.append(app.id)
    
    import logging
    logging.info(f"Usuário {user_id} - Aplicações carregadas: {user_app_ids}")
    logging.info(f"Total de aplicações disponíveis: {len(applications)}")
    
    return render_template('admin/edit_user.html',
                           user=user,
                           groups=groups,
                           applications=applications,
                           user_app_ids=user_app_ids,
                           portal_apps=portal_apps,
                           user_portal_app_ids=user_portal_app_ids,
                           portal_tab_access=user_portal_tab_access)

@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@admin_required
@rate_limit_api()
def admin_delete_user(user_id):
    """Deletar usuário"""
    user = auth_manager.get_user_by_id(user_id)
    if not user:
        flash('Usuário não encontrado.', 'error')
        return redirect(url_for('admin_users'))
    
    # Não permitir deletar a si mesmo
    if user_id == session.get('user_id'):
        flash('Você não pode deletar seu próprio usuário.', 'error')
        return redirect(url_for('admin_users'))
    
    try:
        auth_manager.supabase.table('maestro_users').delete().eq('id', user_id).execute()
        flash('Usuário deletado com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao deletar usuário: {str(e)}', 'error')
    
    return redirect(url_for('admin_users'))

@app.route('/admin/users/<int:user_id>/reset-password', methods=['POST'])
@admin_required
@rate_limit_api()
@csrf.exempt  # Isentar CSRF para requisições AJAX
def admin_reset_password(user_id):
    """Resetar senha do usuário para uma senha temporária"""
    from flask import jsonify
    import secrets
    import string
    
    user = auth_manager.get_user_by_id(user_id)
    if not user:
        return jsonify({'success': False, 'message': 'Usuário não encontrado.'}), 404
    
    # Gerar senha temporária aleatória (12 caracteres: letras maiúsculas, minúsculas e números)
    alphabet = string.ascii_letters + string.digits
    temp_password = ''.join(secrets.choice(alphabet) for i in range(12))
    
    try:
        hashed_password = auth_manager.hash_password(temp_password)
        auth_manager.supabase.table('maestro_users').update({
            'password_hash': hashed_password
        }).eq('id', user_id).execute()
        
        return jsonify({
            'success': True,
            'message': 'Senha resetada com sucesso!',
            'temp_password': temp_password,
            'username': user.get('username', '')
        })
    except Exception as e:
        import logging
        logging.error(f"Erro ao resetar senha: {str(e)}")
        return jsonify({'success': False, 'message': f'Erro ao resetar senha: {str(e)}'}), 500

@app.route('/admin/users/<int:user_id>/toggle-access', methods=['POST'])
@admin_required
@rate_limit_api()
def admin_toggle_application_access(user_id):
    """Conceder ou revogar acesso a uma aplicação (para grupo Operação)"""
    application_id = request.form.get('application_id')
    action = request.form.get('action')  # 'grant' ou 'revoke'
    
    if not application_id or not action:
        flash('Parâmetros inválidos.', 'error')
        return redirect(url_for('admin_edit_user', user_id=user_id))
    
    try:
        if action == 'grant':
            result = auth_manager.grant_application_access(user_id, int(application_id), session.get('user_id'))
        else:
            result = auth_manager.revoke_application_access(user_id, int(application_id))
        
        if result['success']:
            flash(result['message'], 'success')
        else:
            flash(result['message'], 'error')
    except Exception as e:
        flash(f'Erro: {str(e)}', 'error')
    
    return redirect(url_for('admin_edit_user', user_id=user_id))

@app.route('/admin/users/<int:user_id>/update-applications', methods=['POST'])
@admin_required
@rate_limit_api()
def admin_update_applications(user_id):
    """Atualizar múltiplas aplicações de uma vez (para grupo Operação)"""
    import logging
    logging.info(f"Atualizando aplicações para usuário {user_id}")
    logging.info(f"Dados do formulário: {dict(request.form)}")
    
    selected_apps = request.form.getlist('applications')
    logging.info(f"Aplicações selecionadas: {selected_apps}")
    
    try:
        # Obter aplicações atuais do usuário
        current_apps = auth_manager.get_user_applications(user_id)
        current_app_ids = {app['id'] for app in current_apps}
        logging.info(f"Aplicações atuais: {current_app_ids}")
        
        # Converter para inteiros
        selected_app_ids = {int(app_id) for app_id in selected_apps if app_id.isdigit()}
        logging.info(f"Aplicações selecionadas (IDs): {selected_app_ids}")
        
        # Remover aplicações que não estão mais selecionadas
        apps_to_remove = current_app_ids - selected_app_ids
        logging.info(f"Aplicações para remover: {apps_to_remove}")
        for app_id in apps_to_remove:
            auth_manager.revoke_application_access(user_id, app_id)
        
        # Adicionar novas aplicações
        apps_to_add = selected_app_ids - current_app_ids
        logging.info(f"Aplicações para adicionar: {apps_to_add}")
        for app_id in apps_to_add:
            auth_manager.grant_application_access(user_id, app_id, session.get('user_id'))
        
        flash('Aplicações atualizadas com sucesso!', 'success')
    except Exception as e:
        import traceback
        logging.error(f"Erro ao atualizar aplicações: {str(e)}")
        logging.error(traceback.format_exc())
        flash(f'Erro ao atualizar aplicações: {str(e)}', 'error')
    
    return redirect(url_for('admin_edit_user', user_id=user_id))

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
        response.headers['Access-Control-Allow-Origin'] = _get_allowed_origin()
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        return response
    
    # Obter permissões do usuário
    user_id = session.get('user_id')
    user_permissions = auth_manager.get_user_permissions(user_id)
    
    # Preparar aplicações com URL correta (proxy ou direta) e filtrar por permissões
    aplicacoes_preparadas = []
    for app in APLICACOES:
        # Verificar se usuário tem acesso a esta aplicação
        url_proxy = app.get('url_proxy', '')
        if url_proxy:
            try:
                if not auth_manager.has_application_access(user_id, url_proxy):
                    continue  # Pular aplicação se usuário não tiver acesso
            except ServiceUnavailableError:
                continue  # Em caso de Supabase indisponível, não exibir a aplicação
        app_copy = app.copy()
        if USE_PROXY and 'url_proxy' in app:
            app_copy['url_final'] = app['url_proxy']
            app_copy['target_blank'] = False
        else:
            app_copy['url_final'] = app['url']
            app_copy['target_blank'] = True
        aplicacoes_preparadas.append(app_copy)
    
    # Para usuários do grupo "Operacao", adicionar aplicações do portal na tela inicial
    group_name = user_permissions.get('group_name', '').lower()
    if group_name == 'operacao':
        # Buscar aplicações do portal permitidas para o usuário
        portal_apps = auth_manager.get_portal_apps(active_only=True)
        
        # Filtrar aplicações permitidas para este usuário
        if user_permissions.get('is_admin') or user_permissions.get('is_maestro_full'):
            allowed_portal_apps = portal_apps
        else:
            # Buscar aplicações permitidas para o usuário
            user_portal_apps = auth_manager.get_user_portal_apps(user_id)
            permitted_ids = {app.get('id') for app in user_portal_apps if app and app.get('id')}
            allowed_portal_apps = [app for app in portal_apps if app.get('id') in permitted_ids]
        
        # Converter aplicações do portal para o formato das aplicações principais
        # Cores padrão para aplicações do portal (cíano/azul)
        portal_colors = ['#00d4ff', '#06b6d4', '#3b82f6', '#0ea5e9', '#14b8a6']
        for idx, portal_app in enumerate(allowed_portal_apps):
            app_key = portal_app.get('key', '')
            # Extrair o app_key da URL do proxy (ex: /proxy/app-8090 -> app-8090)
            if portal_app.get('url'):
                url_path = portal_app.get('url').lstrip('/proxy/').lstrip('/')
                if url_path:
                    app_key = url_path.split('/')[0]
            
            portal_app_formatted = {
                'nome': portal_app.get('name', 'Aplicação'),
                'url': '',  # Não usar URL direta
                'url_proxy': portal_app.get('url', ''),  # URL do proxy
                'icone': '🗂️',  # Ícone padrão para aplicações do portal
                'cor': portal_colors[idx % len(portal_colors)],  # Rotacionar cores
                'tamanho': 'pequeno'  # Cards pequenos para aplicações do portal
            }
            
            # Processar URL da mesma forma que as aplicações principais
            if USE_PROXY and 'url_proxy' in portal_app_formatted:
                portal_app_formatted['url_final'] = portal_app_formatted['url_proxy']
                portal_app_formatted['target_blank'] = False
            else:
                portal_app_formatted['url_final'] = portal_app_formatted.get('url', '')
                portal_app_formatted['target_blank'] = True
            
            aplicacoes_preparadas.append(portal_app_formatted)
    
    # Adicionar informações do usuário para o template
    user_info = {
        'username': session.get('username'),
        'is_admin': user_permissions.get('is_admin', False),
        'is_maestro_full': user_permissions.get('is_maestro_full', False),
        'group_name': user_permissions.get('group_name', 'N/A'),
        'portal_tab_access': user_permissions.get('portal_tab_access', False)
    }
    
    return render_template('index.html', aplicacoes=aplicacoes_preparadas, user_info=user_info)

@app.route('/applications')
@login_required
def applications_tab():
    """Nova aba de Aplicações do portal (permissão dedicada)"""
    user_id = session.get('user_id')
    user_permissions = auth_manager.get_user_permissions(user_id)

    if not auth_manager.has_portal_tab_access(user_id):
        flash('Você não tem acesso à aba Aplicações.', 'error')
        return redirect(url_for('index'))

    # Buscar todas as aplicações desta aba (ainda sem registros, mas preparado)
    portal_apps = auth_manager.get_portal_apps(active_only=True)

    if user_permissions.get('is_admin') or user_permissions.get('is_maestro_full'):
        allowed_apps = portal_apps
    else:
        permitted_ids = {app.get('id') for app in user_permissions.get('portal_apps', []) if app}
        allowed_apps = [app for app in portal_apps if app.get('id') in permitted_ids]

    return render_template('applications.html', portal_apps=allowed_apps, user_info=user_permissions)


@app.route('/dashboards')
@login_required
def dashboards_tab():
    """Aba Dashboards do portal: quem tem portal_tab_access vê todos os dashboards da aba."""
    user_id = session.get('user_id')
    user_permissions = auth_manager.get_user_permissions(user_id)

    if not auth_manager.has_portal_tab_access(user_id):
        flash('Você não tem acesso à aba Dashboards.', 'error')
        return redirect(url_for('index'))

    allowed_apps = auth_manager.get_portal_dashboards(active_only=True)
    return render_template('dashboards.html', portal_apps=allowed_apps, user_info=user_permissions)

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
        response.headers['Access-Control-Allow-Origin'] = _get_allowed_origin()
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
    
    # Verificar permissão de acesso à aplicação
    # app_key já vem sem /proxy/, então passar diretamente
    user_id = session.get('user_id')
    try:
        if not auth_manager.has_application_access(user_id, app_key):
            logging.warning(f"Usuário {user_id} tentou acessar aplicação {app_key} sem permissão")
            flash('Você não tem permissão para acessar esta aplicação.', 'error')
            return redirect(url_for('index'))
    except ServiceUnavailableError:
        logging.warning("Supabase indisponível ao verificar acesso à aplicação")
        flash('Serviço temporariamente indisponível. Tente novamente em alguns instantes.', 'error')
        return redirect(url_for('index'))
    
    # Log para debug antes de obter target_url
    if app_key == 'apontamento-inspecao-final':
        logging.info(f"Proxy {app_key}: Verificando PROXY_ROUTES...")
        logging.info(f"Proxy {app_key}: PROXY_ROUTES keys: {list(PROXY_ROUTES.keys())}")
    
    target_url = PROXY_ROUTES[app_key]
    
    # Log para debug após obter target_url
    if app_key == 'apontamento-inspecao-final':
        logging.info(f"Proxy {app_key}: target_url obtido: {target_url}")
    
    # Validar URL do proxy (prevenir SSRF)
    if app_key == 'apontamento-inspecao-final':
        logging.info(f"Proxy {app_key}: Validando URL: {target_url}")
    url_valid, url_error = validate_proxy_url(target_url)
    if not url_valid:
        logging.error(f"URL do proxy inválida: {target_url} - {url_error}")
        if app_key == 'apontamento-inspecao-final':
            logging.error(f"Proxy {app_key}: Validação falhou - {url_error}")
        flash('Erro de configuração. Entre em contato com o administrador.', 'error')
        return redirect(url_for('index'))
    if app_key == 'apontamento-inspecao-final':
        logging.info(f"Proxy {app_key}: URL validada com sucesso")
    
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
    elif app_key == 'apontamento-forno':
        # A aplicação está em /apontamento_forno, mas as APIs e estáticos estão na raiz
        if not path or path == 'index.html' or path == 'apontamento_forno.html':
            # Path vazio, index.html ou apontamento_forno.html: acessar /apontamento_forno
            # (a aplicação gerencia esses arquivos internamente)
            full_url = target_url.rstrip('/')
        elif path.startswith('api/') or path.startswith('/api/'):
            # APIs estão na raiz do servidor, não em /apontamento_forno
            # Remover /apontamento_forno da URL base e acessar /api/... diretamente
            base_url = 'http://10.150.16.45:4000'
            clean_path = path.lstrip('/')
            full_url = urljoin(base_url + '/', clean_path)
        elif path.startswith('static/') or path.startswith('/static/'):
            base_url = 'http://10.150.16.45:4000'
            clean_path = path.lstrip('/')
            full_url = urljoin(base_url + '/', clean_path)
        elif path.endswith('.html'):
            # Páginas HTML (colaboradores.html, indicadores.html) na raiz do servidor (4000)
            base_url = 'http://10.150.16.45:4000'
            clean_path = path.lstrip('/')
            full_url = urljoin(base_url + '/', clean_path)
        else:
            # Outros paths em /apontamento_forno/
            clean_path = path.lstrip('/')
            full_url = target_url.rstrip('/') + '/' + clean_path
    elif app_key == 'apontamento-inspecao-final':
        # Aplicação com arquivos estáticos e APIs na raiz do servidor
        # Usar a mesma lógica simples que funciona para gestao-estoque-sap
        if path:
            full_url = urljoin(target_url.rstrip('/') + '/', path)
        else:
            full_url = target_url.rstrip('/') + '/'
    elif app_key == 'dashboard-ocupacao-forno':
        # Aplicação está em /dashboard_ocupacao
        # Recursos estáticos (imagens, CSS, JS) e APIs podem estar na raiz ou em /dashboard_ocupacao
        if not path:
            # Path vazio: acessar /dashboard_ocupacao
            full_url = urljoin(target_url, '/dashboard_ocupacao')
        elif path.startswith('dashboard_ocupacao'):
            # Se o path já começa com dashboard_ocupacao, usar diretamente
            full_url = urljoin(target_url, '/' + path)
        elif path.startswith('api/') or path.startswith('/api/'):
            # APIs podem estar na raiz do servidor
            clean_path = path.lstrip('/')
            full_url = urljoin(target_url + '/', clean_path)
        elif path.endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.webp', '.css', '.js', '.woff', '.woff2', '.ttf', '.eot')):
            # Recursos estáticos: tentar primeiro na raiz, depois em /dashboard_ocupacao
            # Primeiro tenta na raiz (mais comum)
            clean_path = path.lstrip('/')
            full_url = urljoin(target_url + '/', clean_path)
        elif path.startswith('forno_') or path.startswith('/forno_'):
            # Endpoints de API que começam com forno_ estão na raiz do servidor
            # Exemplos: /forno_fator_pecas, /forno_fator_ciclos
            clean_path = path.lstrip('/')
            full_url = urljoin(target_url + '/', clean_path)
        elif '.' not in path or path.endswith('.html'):
            # Paths sem extensão ou com .html: podem ser páginas HTML em /dashboard_ocupacao
            # Mas se não tiver extensão e não começar com forno_, pode ser uma API na raiz
            # Por segurança, tentar primeiro na raiz (mais comum para APIs)
            clean_path = path.lstrip('/')
            full_url = urljoin(target_url + '/', clean_path)
        else:
            # Outros paths: adicionar /dashboard_ocupacao antes
            clean_path = path.lstrip('/')
            full_url = urljoin(target_url, '/dashboard_ocupacao/' + clean_path)
    elif app_key == 'dashboard-ocupacao-hoje':
        # Aplicação está em /dashboard_ocupacao_hoje
        # Recursos estáticos (imagens, CSS, JS) e APIs podem estar na raiz ou em /dashboard_ocupacao_hoje
        if not path:
            # Path vazio: acessar /dashboard_ocupacao_hoje
            full_url = urljoin(target_url, '/dashboard_ocupacao_hoje')
        elif path.startswith('dashboard_ocupacao_hoje'):
            # Se o path já começa com dashboard_ocupacao_hoje, usar diretamente
            full_url = urljoin(target_url, '/' + path)
        elif path.startswith('api/') or path.startswith('/api/'):
            # APIs podem estar na raiz do servidor
            clean_path = path.lstrip('/')
            full_url = urljoin(target_url + '/', clean_path)
        elif path.endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.webp', '.css', '.js', '.woff', '.woff2', '.ttf', '.eot')):
            # Recursos estáticos: tentar primeiro na raiz
            clean_path = path.lstrip('/')
            full_url = urljoin(target_url + '/', clean_path)
        elif path.startswith('forno_') or path.startswith('/forno_'):
            # Endpoints de API que começam com forno_ estão na raiz do servidor
            clean_path = path.lstrip('/')
            full_url = urljoin(target_url + '/', clean_path)
        elif '.' not in path or path.endswith('.html'):
            # Paths sem extensão ou com .html: podem ser páginas HTML em /dashboard_ocupacao_hoje
            # Mas se não tiver extensão e não começar com forno_, pode ser uma API na raiz
            clean_path = path.lstrip('/')
            full_url = urljoin(target_url + '/', clean_path)
        else:
            # Outros paths: adicionar /dashboard_ocupacao_hoje antes
            clean_path = path.lstrip('/')
            full_url = urljoin(target_url, '/dashboard_ocupacao_hoje/' + clean_path)
    elif path:
        # Para gestao-estoque-sap e outras aplicações padrão, garantir que o path seja tratado corretamente
        clean_path = path.lstrip('/')
        if app_key == 'gestao-estoque-sap':
            # Para gestao-estoque-sap, usar construção direta para evitar problemas com urljoin
            full_url = target_url.rstrip('/') + '/' + clean_path
        else:
            full_url = urljoin(target_url + '/', path)
    else:
        full_url = target_url + '/'
    
    # Adicionar query string se houver
    if request.query_string:
        full_url += '?' + request.query_string.decode('utf-8')
    
    # Log para debug (apenas para apontamento-inspecao-final e gestao-estoque-sap)
    if app_key == 'apontamento-inspecao-final' or app_key == 'gestao-estoque-sap':
        logging.info(f"Proxy {app_key}: {request.method} path='{path}' -> full_url='{full_url}'")
        logging.info(f"Proxy {app_key}: target_url='{target_url}'")
        logging.info(f"Proxy {app_key}: request.url='{request.url}', request.path='{request.path}'")
    
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
        
        # Definir se deve verificar certificado (para self-signed em alguns hosts)
        verify_cert = PROXY_VERIFY.get(app_key, True)
        
        # Desabilitar warnings SSL quando verify=False (para self-signed certificates)
        if not verify_cert:
            try:
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            except ImportError:
                pass  # urllib3 pode não estar disponível
        
        # Log adicional para debug de aplicações HTTPS
        if app_key == 'apontamento-inspecao-final':
            logging.info(f"Proxy {app_key}: verify_cert={verify_cert}")
            logging.info(f"Proxy {app_key}: target_url={target_url}, full_url={full_url}")
            logging.info(f"Proxy {app_key}: method={method}, headers keys={list(headers.keys())[:5]}...")

        # Fazer requisição usando pool de conexões
        try:
            response = http_session.request(
                method=method,
                url=full_url,
                headers=headers,
                data=data,
                files=files,
                params=params,
                stream=True,
                timeout=30,
                allow_redirects=False,
                verify=verify_cert
            )
            # Apontamento Forno: se .html retornar 404, redirecionar para index.html?view=XXX (SPA usa query)
            if (app_key == 'apontamento-forno' and method == 'GET' and path.endswith('.html')
                    and path not in ('index.html', 'apontamento_forno.html') and response.status_code == 404):
                view_name = path[:-5] if len(path) > 5 else path.replace('.html', '')
                if view_name:
                    redirect_to = url_for('proxy_app', app_key=app_key, path='index.html', _external=True)
                    if '?' in redirect_to:
                        redirect_to += '&view=' + view_name
                    else:
                        redirect_to += '?view=' + view_name
                    logging.info(f"Proxy {app_key}: 404 para {path} -> redirect index.html?view={view_name}")
                    return redirect(redirect_to)
        except requests.exceptions.SSLError as ssl_error:
            logging.error(f"Erro SSL no proxy para {app_key}: {str(ssl_error)}")
            logging.error(f"URL: {full_url}, verify_cert={verify_cert}")
            raise
        except requests.exceptions.ConnectionError as conn_error:
            logging.error(f"Erro de conexão no proxy para {app_key}: {str(conn_error)}")
            logging.error(f"URL: {full_url}")
            raise
        except Exception as req_error:
            logging.error(f"Erro na requisição para {app_key}: {type(req_error).__name__}: {str(req_error)}")
            logging.error(f"URL: {full_url}, verify_cert={verify_cert}")
            raise
        
        # Log de resposta para debug
        if app_key == 'apontamento-inspecao-final':
            logging.info(f"Proxy {app_key}: Response status={response.status_code}, Content-Type={response.headers.get('Content-Type', 'N/A')}")
            if response.status_code >= 400:
                logging.warning(f"Proxy {app_key}: Erro HTTP {response.status_code} de {full_url}")
        
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
        
        # Ajustar permissões para permitir câmera e microfone via proxy
        # Remover políticas restritivas vindas da origem e setar política permissiva em formato válido
        response_headers.pop('Permissions-Policy', None)
        response_headers.pop('Permission-Policy', None)  # variantes antigas
        response_headers.pop('Feature-Policy', None)     # legado
        # Formato aceito: string única com vírgulas separando as políticas
        # Usar self (maestro.opera.security) e URLs específicas das aplicações que usam câmera
        # IMPORTANTE: usar string única, não tupla Python
        # Formato válido: camera=(self https://...), microphone=(self https://...), ...
        permissions_policy_value = 'camera=(self "https://maestro.opera.security" "https://10.150.16.45:8091" "https://10.150.16.45:9010"), microphone=(self "https://maestro.opera.security" "https://10.150.16.45:8091" "https://10.150.16.45:9010"), geolocation=(self "https://maestro.opera.security"), fullscreen=*, clipboard-read=*, clipboard-write=*'
        response_headers['Permissions-Policy'] = permissions_policy_value
        
        # Remover CSP da aplicação proxyada (vamos controlar isso no Maestro)
        response_headers.pop('Content-Security-Policy', None)
        response_headers.pop('X-Content-Security-Policy', None)
        response_headers.pop('X-WebKit-CSP', None)
        
        # CORS: mesma origem (nunca * com credentials)
        if 'Access-Control-Allow-Origin' not in response_headers:
            response_headers['Access-Control-Allow-Origin'] = _get_allowed_origin()
        
        # Adicionar headers de cache para arquivos estáticos (melhora performance e reduz erros intermitentes)
        path_lower = path.lower()
        if path_lower.endswith(('.js', '.mjs', '.css', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.webp', '.woff', '.woff2', '.ttf', '.eot')):
            # Cache por 1 hora para arquivos estáticos (ajuda com imports dinâmicos intermitentes)
            if 'Cache-Control' not in response_headers:
                response_headers['Cache-Control'] = 'public, max-age=3600, must-revalidate'
            if 'ETag' not in response_headers and response.status_code == 200:
                # Adicionar ETag simples baseado no path e timestamp (ajuda com validação de cache)
                etag = hashlib.md5(f"{path}_{response.status_code}".encode()).hexdigest()
                response_headers['ETag'] = f'"{etag}"'
        
        # Preservar MIME type correto baseado na extensão do arquivo
        # Isso é importante para CSS, JS, imagens, etc.
        content_type = response_headers.get('Content-Type', '').lower()
        
        # Se não houver Content-Type ou for genérico, tentar detectar pelo path
        if not content_type or 'text/html' in content_type or 'application/octet-stream' in content_type:
            path_lower = path.lower()
            if path_lower.endswith('.css'):
                content_type = 'text/css'
                response_headers['Content-Type'] = 'text/css; charset=utf-8'
            elif path_lower.endswith('.js') or path_lower.endswith('.mjs'):
                # Garantir Content-Type correto para JavaScript (imports dinâmicos precisam disso)
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
                
                # 1.0. Para dashboard-ocupacao-forno e dashboard-ocupacao-hoje, capturar recursos estáticos na raiz
                if app_key == 'dashboard-ocupacao-forno' or app_key == 'dashboard-ocupacao-hoje':
                    static_extensions = ['.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.webp', '.woff', '.woff2', '.ttf', '.eot']
                    ext_pattern = '|'.join([re.escape(ext) for ext in static_extensions])
                    
                    # Capturar recursos estáticos que começam com / (ex: /information.png, /styles.css)
                    pattern = rf'(href|src|action|data-src|data-href|data-url|data-action|background|background-image)\s*=\s*(["\']?)(/[^"\'>\s]*\.(?:{ext_pattern}))(["\']?)'
                    def replace_dashboard_static(match):
                        attr = match.group(1)
                        quote = match.group(2)
                        url = match.group(3)
                        end_quote = match.group(4)
                        # Se não começar com /proxy/ e não for /dashboard_ocupacao, adicionar proxy_base
                        if (not url.startswith(proxy_base) and 
                            not url.startswith('/dashboard_ocupacao') and 
                            not url.startswith('/login') and 
                            not url.startswith('/logout') and 
                            not url.startswith('/static/')):
                            return f'{attr}={quote}{proxy_base}{url}{end_quote}'
                        return match.group(0)
                    
                    content = re.sub(
                        pattern,
                        replace_dashboard_static,
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
                        # Para dashboard-ocupacao-forno e outras apps, reescrever para passar pelo proxy
                        # URLs que começam com /dashboard_ocupacao precisam passar pelo proxy
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
                    # Para dashboard-ocupacao-forno, recursos estáticos na raiz não precisam de /dashboard_ocupacao
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
                    # Para dashboard-ocupacao-forno, recursos estáticos na raiz não precisam de /dashboard_ocupacao
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
    // Quando estamos numa página do proxy (ex: /proxy/portal-procedimentos/), /static/ deve ir para o backend da app, não do Maestro
    const isProxyPage = window.location.pathname.startsWith(PROXY_BASE);
    
    // Função para verificar se uma URL deve ser redirecionada para o proxy
    function shouldProxy(url) {{
        if (typeof url !== 'string') return false;
        
        // Verificar se é URL absoluta que aponta para o próprio domínio
        try {{
            const urlObj = new URL(url, window.location.origin);
            const currentOrigin = window.location.origin;
            // Se a URL absoluta aponta para o mesmo domínio, tratar como relativa
            if (urlObj.origin === currentOrigin) {{
                url = urlObj.pathname + (urlObj.search || '') + (urlObj.hash || '');
            }} else {{
                // URL absoluta para outro domínio - não proxy
                return false;
            }}
        }} catch (e) {{
            // Se não conseguir fazer parse, tratar como relativa
        }}
        
        // Não proxy URLs que já estão no proxy
        if (url.startsWith(PROXY_BASE)) return false;
        // Não proxy URLs do próprio Maestro (login, logout; /static/ só quando NÃO estamos numa app proxyada)
        if (url.startsWith('/login') || url.startsWith('/logout')) return false;
        if (url.startsWith('/static/') && !isProxyPage) return false;
        // Proxy todas as outras URLs relativas (incluindo /, /api/, /static/ quando isProxyPage, etc.)
        return url.startsWith('/') || url === '';
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
    
    // Interceptar fetch() - interceptação mais agressiva para APIs
    const originalFetch = window.fetch;
    window.fetch = function(url, options) {{
        const originalUrl = url;
        let finalUrl = url;
        const currentOrigin = window.location.origin;
        
        // Função auxiliar para processar URL
        function processUrl(urlString) {{
            if (!urlString || typeof urlString !== 'string') return urlString;
            
            try {{
                const urlObj = new URL(urlString, currentOrigin);
                // Se a URL aponta para o mesmo domínio, processar
                if (urlObj.origin === currentOrigin) {{
                    let path = urlObj.pathname + (urlObj.search || '') + (urlObj.hash || '');
                    // Não interceptar URLs do Maestro (login, logout; /static/ só quando NÃO estamos numa app proxyada)
                    if (path.startsWith('/login') || path.startsWith('/logout')) {{
                        return urlString; // Retornar original
                    }}
                    if (path.startsWith('/static/') && !isProxyPage) {{
                        return urlString; // Arquivos estáticos do Maestro
                    }}
                    // Não interceptar se já está no proxy
                    if (path.startsWith(PROXY_BASE)) {{
                        return urlString; // Retornar original
                    }}
                    // Interceptar todas as outras URLs do mesmo domínio (incluindo /, /api/, etc.)
                    if (path === '' || path === '/') {{
                        return PROXY_BASE + '/';
                    }} else {{
                        return PROXY_BASE + path;
                    }}
                }}
            }} catch (e) {{
                // Se não conseguir fazer parse, tratar como relativa
                const skipStatic = urlString.startsWith('/static/') && !isProxyPage;
                if (urlString.startsWith('/') && !urlString.startsWith('/login') && !urlString.startsWith('/logout') && !skipStatic && !urlString.startsWith(PROXY_BASE)) {{
                    if (urlString === '/') {{
                        return PROXY_BASE + '/';
                    }} else {{
                        return PROXY_BASE + urlString;
                    }}
                }}
            }}
            return urlString; // Retornar original se não precisar interceptar
        }}
        
        // Processar URL baseado no tipo
        if (typeof url === 'string') {{
            finalUrl = processUrl(url);
            if (finalUrl !== originalUrl) {{
                console.log('[Maestro Proxy] Interceptando fetch (string):', originalUrl, '->', finalUrl);
            }}
        }} else if (url instanceof Request) {{
            const processedUrl = processUrl(url.url);
            if (processedUrl !== url.url) {{
                console.log('[Maestro Proxy] Interceptando fetch (Request):', url.url, '->', processedUrl);
                // IMPORTANTE: Quando criamos um novo Request, precisamos passar o objeto Request original
                // como segundo parâmetro para preservar todas as propriedades (método, headers, body, etc.)
                // O construtor Request aceita um objeto Request como segundo parâmetro e copia todas as propriedades
                finalUrl = new Request(processedUrl, url);
            }} else {{
                finalUrl = url;
            }}
        }}
        
        // Se ainda assim for vazio ou raiz, forçar proxy base
        if (typeof finalUrl === 'string' && (finalUrl === '' || finalUrl === '/' || finalUrl === currentOrigin || finalUrl === currentOrigin + '/')) {{
            const forced = PROXY_BASE + '/';
            console.warn('[Maestro Proxy] Forçando proxy para requisição vazia/raiz:', originalUrl, '->', forced);
            finalUrl = forced;
        }}
        
        // Verificação final: se a URL final ainda aponta para a raiz do Maestro, forçar proxy
        if (typeof finalUrl === 'string') {{
            try {{
                const finalUrlObj = new URL(finalUrl, currentOrigin);
                if (finalUrlObj.origin === currentOrigin && (finalUrlObj.pathname === '/' || finalUrlObj.pathname === '')) {{
                    if (!finalUrl.startsWith(PROXY_BASE)) {{
                        const forced = PROXY_BASE + '/';
                        console.error('[Maestro Proxy] ERRO: URL ainda aponta para raiz após processamento!', originalUrl, '->', forced);
                        finalUrl = forced;
                    }}
                }}
            }} catch (e) {{
                // Ignorar erros de parsing
            }}
        }}
        
        // Log final para debug (apenas para apontamento-inspecao-final)
        const isInspecaoFinal = window.location.pathname.includes('apontamento-inspecao-final');
        if (isInspecaoFinal) {{
            const method = options?.method || (finalUrl instanceof Request ? finalUrl.method : 'GET');
            const urlStr = typeof finalUrl === 'string' ? finalUrl : (finalUrl instanceof Request ? finalUrl.url : String(finalUrl));
            console.log('[Maestro Proxy] Fetch final:', {{
                original: typeof originalUrl === 'string' ? originalUrl : (originalUrl instanceof Request ? originalUrl.url : String(originalUrl)),
                final: urlStr,
                method: method,
                hasBody: !!(options?.body || (finalUrl instanceof Request ? finalUrl.body : null))
            }});
        }}
        
        return originalFetch.call(this, finalUrl, options);
    }};
    
    // Interceptar também antes do DOM estar pronto (executar imediatamente)
    console.log('[Maestro Proxy] Script carregado, PROXY_BASE =', PROXY_BASE);
    
    // Garantir que a interceptação está ativa
    // Verificar periodicamente se fetch foi sobrescrito (a cada 100ms)
    setInterval(function() {{
        if (window.fetch !== originalFetch && !window.fetch.toString().includes('PROXY_BASE')) {{
            console.warn('[Maestro Proxy] fetch foi sobrescrito, reaplicando interceptação');
            // Reaplicar interceptação (o código já está acima)
        }}
    }}, 100);
    
    // Interceptar XMLHttpRequest - interceptação mais agressiva
    const originalOpen = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function(method, url, async, user, password) {{
        const originalUrl = url;
        const currentOrigin = window.location.origin;
        
        // Processar URL similar ao fetch
        if (typeof url === 'string') {{
            try {{
                const urlObj = new URL(url, currentOrigin);
                if (urlObj.origin === currentOrigin) {{
                    let path = urlObj.pathname + (urlObj.search || '') + (urlObj.hash || '');
                    const skipStatic = path.startsWith('/static/') && !isProxyPage;
                    if (!path.startsWith('/login') && !path.startsWith('/logout') && !skipStatic && !path.startsWith(PROXY_BASE)) {{
                        if (path === '' || path === '/') {{
                            url = PROXY_BASE + '/';
                        }} else {{
                            url = PROXY_BASE + path;
                        }}
                        console.log('[Maestro Proxy] Interceptando XHR:', originalUrl, '->', url);
                    }}
                }}
            }} catch (e) {{
                const skipStatic = url.startsWith('/static/') && !isProxyPage;
                if (url.startsWith('/') && !url.startsWith('/login') && !url.startsWith('/logout') && !skipStatic && !url.startsWith(PROXY_BASE)) {{
                    if (url === '/') {{
                        url = PROXY_BASE + '/';
                    }} else {{
                        url = PROXY_BASE + url;
                    }}
                    console.log('[Maestro Proxy] Interceptando XHR (relativa):', originalUrl, '->', url);
                }}
            }}
        }}

        // Se ainda assim for vazio ou raiz, forçar proxy base
        if (url === '' || url === '/' || url === currentOrigin || url === currentOrigin + '/') {{
            const forced = PROXY_BASE + '/';
            console.warn('[Maestro Proxy] Forçando proxy XHR para requisição vazia/raiz:', originalUrl, '->', forced);
            url = forced;
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
    
    // IMPORTANTE: O fetch() interceptado acima já captura imports dinâmicos (import())
    // porque o navegador usa fetch internamente para carregar módulos ES6.
    // As melhorias no servidor (Content-Type correto, headers de cache) devem
    // resolver o problema intermitente de "Failed to fetch dynamically imported module"
    
    console.log('[Maestro Proxy] Interceptação completa configurada (fetch, XHR, jQuery)');
    console.log('[Maestro Proxy] Imports dinâmicos serão interceptados automaticamente via fetch');
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
                logging.warning(f"Erro ao processar HTML do proxy: {str(e)}")
                # Se der erro, retornar conteúdo original
                return Response(
                    stream_with_context(generate()),
                    status=response.status_code,
                    headers=response_headers
                )
        else:
            # Para outros tipos de conteúdo (CSS, JS, imagens, JSON, etc.), retornar como está
            # Mas garantir que o MIME type esteja correto
            mimetype = None
            if 'Content-Type' in response_headers:
                mimetype = response_headers['Content-Type'].split(';')[0].strip()
            
            # Garantir Content-Type correto para arquivos JavaScript (crítico para imports dinâmicos)
            path_lower = path.lower()
            if path_lower.endswith('.js') or path_lower.endswith('.mjs'):
                if not mimetype or 'javascript' not in mimetype.lower():
                    mimetype = 'application/javascript'
                    response_headers['Content-Type'] = 'application/javascript; charset=utf-8'
            
            # Para respostas de erro (4xx, 5xx) que não são HTML, preservar o Content-Type original
            # Isso é importante para APIs que retornam JSON mesmo em erros
            if response.status_code >= 400 and mimetype and 'text/html' not in mimetype.lower():
                # Preservar o Content-Type original para APIs (JSON, etc.)
                pass  # mimetype já está correto
            
            return Response(
                stream_with_context(generate()),
                status=response.status_code,
                headers=response_headers,
                mimetype=mimetype
            )
        
    except requests.exceptions.RequestException as e:
        import traceback
        error_details = traceback.format_exc()
        logging.error(f"Erro no proxy para {app_key}: {str(e)}")
        logging.error(f"URL tentada: {full_url}")
        logging.error(f"Detalhes do erro: {error_details}")
        log_proxy_access(app_key, path, 500)
        
        # Para requisições de API (PUT, POST, DELETE, PATCH), retornar JSON em vez de redirect
        if request.method in ['PUT', 'POST', 'DELETE', 'PATCH'] or path.startswith('api/'):
            error_message = str(e)
            # Extrair mensagem mais específica se possível
            if 'too many 500 error responses' in error_message:
                error_message = 'O servidor da aplicação está retornando erros. Tente novamente mais tarde.'
            elif 'Connection' in error_message or 'timeout' in error_message.lower():
                error_message = 'Não foi possível conectar ao servidor da aplicação. Verifique se o servidor está online.'
            
            return Response(
                json.dumps({
                    'success': False,
                    'error': error_message,
                    'details': 'Erro ao processar requisição no servidor de destino'
                }),
                status=500,
                mimetype='application/json',
                headers={
                    'Access-Control-Allow-Origin': _get_allowed_origin(),
                    'Content-Type': 'application/json'
                }
            )
        
        # Para requisições GET (páginas HTML), fazer redirect
        flash(f'Erro ao acessar a aplicação. Tente novamente.', 'error')
        return redirect(url_for('index'))
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logging.error(f"Erro inesperado no proxy para {app_key}: {str(e)}")
        logging.error(f"URL tentada: {full_url if 'full_url' in locals() else 'N/A'}")
        logging.error(f"Detalhes do erro: {error_details}")
        log_proxy_access(app_key, path, 500)
        
        # Para requisições de API (PUT, POST, DELETE, PATCH), retornar JSON em vez de redirect
        if request.method in ['PUT', 'POST', 'DELETE', 'PATCH'] or path.startswith('api/'):
            return Response(
                json.dumps({
                    'success': False,
                    'error': 'Erro inesperado ao processar requisição',
                    'details': str(e)
                }),
                status=500,
                mimetype='application/json',
                headers={
                    'Access-Control-Allow-Origin': _get_allowed_origin(),
                    'Content-Type': 'application/json'
                }
            )
        
        # Para requisições GET (páginas HTML), fazer redirect
        flash(f'Erro ao acessar a aplicação. Tente novamente.', 'error')
        return redirect(url_for('index'))

if __name__ == '__main__':
    # Configurações para produção em Docker
    port = int(os.environ.get('PORT', 8000))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    app.run(host=host, port=port, debug=debug)
