"""
Sistema de Autenticação Avançado com Supabase
"""
from flask import session, redirect, url_for, flash
from functools import wraps
from supabase import create_client, Client
import bcrypt
import os
from dotenv import load_dotenv

load_dotenv()


class ServiceUnavailableError(Exception):
    """Erro quando o Supabase/PostgREST está temporariamente indisponível (ex.: 503, PGRST002)."""
    pass


class AuthManager:
    """Gerenciador de autenticação com Supabase"""
    
    def __init__(self):
        # Obtém variáveis de ambiente e remove caracteres de controle (como \r do Windows)
        supabase_url = os.getenv('SUPABASE_URL', '').strip().replace('\r', '').replace('\n', '')
        supabase_key = (os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_KEY') or '').strip().replace('\r', '').replace('\n', '')
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY devem estar configurados no .env")
        
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
    
    def hash_password(self, password: str) -> str:
        """Gera hash bcrypt da senha"""
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verifica se a senha corresponde ao hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception:
            return False
    
    def create_user(self, username: str, password: str, email: str = None) -> dict:
        """Cria um novo usuário no banco de dados"""
        try:
            hashed_password = self.hash_password(password)
            
            # Verifica se usuário já existe
            existing = self.supabase.table('maestro_users').select('id').eq('username', username).execute()
            if existing.data:
                return {'success': False, 'message': 'Usuário já existe'}
            
            # Insere novo usuário
            user_data = {
                'username': username,
                'password_hash': hashed_password,
                'email': email or f"{username}@opera.com",
                'active': True
            }
            
            result = self.supabase.table('maestro_users').insert(user_data).execute()
            
            if result.data:
                return {
                    'success': True,
                    'message': 'Usuário criado com sucesso',
                    'user_id': result.data[0]['id']
                }
            else:
                return {'success': False, 'message': 'Erro ao criar usuário'}
                
        except Exception as e:
            return {'success': False, 'message': f'Erro: {str(e)}'}
    
    def authenticate(self, username: str, password: str) -> dict:
        """Autentica usuário e retorna dados do usuário"""
        try:
            # Normaliza username (case-insensitive)
            username_lower = username.lower().strip()
            
            # Busca usuário no banco (case-insensitive)
            result = self.supabase.table('maestro_users').select('*').ilike('username', username_lower).execute()
            
            if not result.data:
                # Tenta busca exata também
                result = self.supabase.table('maestro_users').select('*').eq('username', username.strip()).execute()
            
            if not result.data:
                return {'success': False, 'message': 'Usuário ou senha inválidos'}
            
            user = result.data[0]
            
            # Verifica se usuário está ativo
            if not user.get('active', True):
                return {'success': False, 'message': 'Usuário inativo. Entre em contato com o administrador.'}
            
            # Verifica senha
            if not self.verify_password(password, user['password_hash']):
                return {'success': False, 'message': 'Usuário ou senha inválidos'}
            
            # Atualiza último login
            try:
                from datetime import datetime
                self.supabase.table('maestro_users').update({
                    'last_login': datetime.utcnow().isoformat()
                }).eq('id', user['id']).execute()
            except Exception:
                pass  # Não falha se não conseguir atualizar
            
            # Remove senha do retorno
            user.pop('password_hash', None)
            
            return {
                'success': True,
                'user': user
            }
            
        except Exception as e:
            # Log do erro com mais detalhes para debug
            import logging
            error_msg = str(e)
            logging.error(f"Erro na autenticação: {error_msg}")
            
            # Verificar se é erro de API key
            if 'Invalid API key' in error_msg or '401' in error_msg:
                logging.error("⚠️  Erro de autenticação com Supabase - verifique SUPABASE_SERVICE_ROLE_KEY no .env")
                return {'success': False, 'message': 'Erro de configuração. Entre em contato com o administrador.'}
            
            # Supabase temporariamente indisponível (503 / PGRST002)
            if '503' in error_msg or 'PGRST002' in error_msg or 'schema cache' in error_msg.lower():
                return {'success': False, 'message': 'Serviço temporariamente indisponível. Tente novamente em alguns instantes.'}
            
            return {'success': False, 'message': 'Erro ao processar autenticação. Tente novamente.'}
    
    def get_user_by_id(self, user_id: int) -> dict:
        """Busca usuário por ID"""
        try:
            result = self.supabase.table('maestro_users').select('*').eq('id', user_id).execute()
            if result.data:
                user = result.data[0]
                user.pop('password_hash', None)
                return user
            return None
        except Exception:
            return None
    
    def get_user_group(self, user_id: int) -> dict:
        """Busca grupo do usuário"""
        try:
            result = self.supabase.table('maestro_users').select(
                'id, username, group_id, maestro_user_groups(id, name, description)'
            ).eq('id', user_id).execute()
            
            if result.data and result.data[0].get('maestro_user_groups'):
                group_data = result.data[0]['maestro_user_groups']
                if isinstance(group_data, list) and len(group_data) > 0:
                    return group_data[0]
                elif isinstance(group_data, dict):
                    return group_data
            return None
        except Exception as e:
            import logging
            logging.error(f"Erro ao buscar grupo do usuário: {str(e)}")
            return None
    
    def is_admin(self, user_id: int) -> bool:
        """Verifica se usuário é administrador"""
        group = self.get_user_group(user_id)
        return group and group.get('name') == 'administrador'
    
    def is_maestro_full(self, user_id: int) -> bool:
        """Verifica se usuário tem acesso completo (Maestro Full)"""
        group = self.get_user_group(user_id)
        return group and group.get('name') == 'maestro_full'
    
    def has_portal_tab_access(self, user_id: int) -> bool:
        """Verifica se usuário pode acessar a nova aba 'Aplicações' do portal"""
        # Apenas Administrador tem acesso automático; Maestro Full usa o flag no usuário
        if self.is_admin(user_id):
            return True
        user = self.get_user_by_id(user_id)
        return bool(user and user.get('portal_tab_access'))

    def get_portal_apps(self, active_only: bool = True) -> list:
        """Retorna as aplicações cadastradas na aba Aplicações (maestro_portal_applications)."""
        try:
            query = self.supabase.table('maestro_portal_applications').select('*')
            if active_only:
                query = query.eq('active', True)
            result = query.order('name').execute()
            return result.data or []
        except Exception as e:
            import logging
            logging.error(f"Erro ao buscar portal apps: {str(e)}")
            return []

    def get_portal_dashboards(self, active_only: bool = True) -> list:
        """Retorna os dashboards cadastrados na aba Dashboards (maestro_portal_dashboards)."""
        try:
            query = self.supabase.table('maestro_portal_dashboards').select('*')
            if active_only:
                query = query.eq('active', True)
            result = query.order('name').execute()
            return result.data or []
        except Exception as e:
            import logging
            logging.error(f"Erro ao buscar portal dashboards: {str(e)}")
            return []

    def get_user_portal_apps(self, user_id: int) -> list:
        """Retorna as aplicações da nova aba permitidas para o usuário"""
        try:
            result = self.supabase.table('maestro_user_portal_app_access').select(
                'portal_app_id, maestro_portal_applications(id, key, name, description, active)'
            ).eq('user_id', user_id).execute()
            apps = []
            for item in result.data or []:
                app = item.get('maestro_portal_applications')
                if isinstance(app, list) and app:
                    app = app[0]
                if isinstance(app, dict):
                    apps.append(app)
            return apps
        except Exception as e:
            import logging
            logging.error(f"Erro ao buscar portal apps do usuário: {str(e)}")
            return []

    def set_user_portal_apps(self, user_id: int, portal_app_ids: list, granted_by: int = None) -> bool:
        """Define (substitui) as aplicações da nova aba permitidas para o usuário"""
        try:
            # Limpa permissões existentes
            self.supabase.table('maestro_user_portal_app_access').delete().eq('user_id', user_id).execute()
            # Insere novas permissões
            if portal_app_ids:
                rows = [{
                    'user_id': user_id,
                    'portal_app_id': app_id,
                    'granted_by': granted_by
                } for app_id in portal_app_ids]
                self.supabase.table('maestro_user_portal_app_access').insert(rows).execute()
            return True
        except Exception as e:
            import logging
            logging.error(f"Erro ao definir portal apps do usuário: {str(e)}")
            return False

    def update_portal_tab_access(self, user_id: int, enabled: bool) -> bool:
        """Atualiza flag de acesso à aba de Aplicações"""
        try:
            self.supabase.table('maestro_users').update({'portal_tab_access': enabled}).eq('id', user_id).execute()
            return True
        except Exception as e:
            import logging
            logging.error(f"Erro ao atualizar portal_tab_access: {str(e)}")
            return False

    def has_application_access(self, user_id: int, url_proxy: str) -> bool:
        """Verifica se usuário tem acesso a uma aplicação específica"""
        try:
            # Administrador e Maestro Full têm acesso a tudo
            if self.is_admin(user_id) or self.is_maestro_full(user_id):
                return True
            
            # Para grupo Operação, verificar permissões específicas
            # Extrair o nome da aplicação do url_proxy
            # url_proxy pode vir como '/proxy/painel-monitoracao' ou 'painel-monitoracao'
            app_key = url_proxy
            if app_key.startswith('/proxy/'):
                app_key = app_key.replace('/proxy/', '')
            elif app_key.startswith('proxy/'):
                app_key = app_key.replace('proxy/', '')
            
            # 1) Tentar nas aplicações principais
            app_result = self.supabase.table('maestro_applications').select('id').eq('url_proxy', app_key).eq('active', True).execute()
            if app_result.data:
                app_id = app_result.data[0]['id']
                access_result = self.supabase.table('maestro_user_application_access').select('id').eq('user_id', user_id).eq('application_id', app_id).execute()
                return len(access_result.data) > 0

            # 2) Tentar na tabela de Dashboards (aba Dashboards: quem tem portal_tab_access vê todos)
            dashboard = self.supabase.table('maestro_portal_dashboards').select('id').eq('key', app_key).eq('active', True).execute()
            if dashboard.data:
                user = self.get_user_by_id(user_id)
                return bool(user and user.get('portal_tab_access'))

            # 3) Tentar nas aplicações da aba Aplicações (portal)
            portal_app = self.supabase.table('maestro_portal_applications').select('id').eq('key', app_key).eq('active', True).execute()
            if portal_app.data:
                portal_app_id = portal_app.data[0]['id']
                user = self.get_user_by_id(user_id)
                portal_enabled = bool(user and user.get('portal_tab_access'))
                if not portal_enabled:
                    return False
                access_result = self.supabase.table('maestro_user_portal_app_access').select('id').eq('user_id', user_id).eq('portal_app_id', portal_app_id).execute()
                return len(access_result.data) > 0

            import logging
            logging.warning(f"Aplicação não encontrada para app_key/url_proxy: {app_key}")
            return False
        except Exception as e:
            import logging
            error_msg = str(e)
            logging.error(f"Erro ao verificar acesso à aplicação: {error_msg}")
            # Supabase/PostgREST indisponível: permitir que o chamador exiba mensagem amigável
            if '503' in error_msg or 'PGRST002' in error_msg or 'schema cache' in error_msg.lower():
                raise ServiceUnavailableError("Supabase temporariamente indisponível") from e
            import traceback
            logging.error(traceback.format_exc())
            return False
    
    def get_user_permissions(self, user_id: int) -> dict:
        """Retorna todas as permissões do usuário"""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return {'is_admin': False, 'is_maestro_full': False, 'applications': []}
            
            group = self.get_user_group(user_id)
            group_name = group.get('name') if group else None
            
            is_admin = group_name == 'administrador'
            is_maestro_full = group_name == 'maestro_full'
            
            applications = []
            if not is_admin and not is_maestro_full:
                # Para grupo Operação, buscar aplicações permitidas
                result = self.supabase.table('maestro_user_application_access').select(
                    'application_id, maestro_applications(id, name, url_proxy, display_name, icon, color)'
                ).eq('user_id', user_id).execute()
                
                for item in result.data:
                    if item.get('maestro_applications'):
                        app = item['maestro_applications']
                        if isinstance(app, list) and len(app) > 0:
                            app = app[0]
                        applications.append({
                            'id': app.get('id'),
                            'url_proxy': app.get('url_proxy'),
                            'name': app.get('name'),
                            'display_name': app.get('display_name'),
                            'icon': app.get('icon'),
                            'color': app.get('color')
                        })
            
            return {
                'is_admin': is_admin,
                'is_maestro_full': is_maestro_full,
                'group_name': group_name,
                'group_id': group.get('id') if group else None,
                'applications': applications,
                'portal_tab_access': True if is_admin else bool(user.get('portal_tab_access', False)),
                'portal_apps': self.get_user_portal_apps(user_id) if not (is_admin or is_maestro_full) else self.get_portal_apps(active_only=True)
            }
        except Exception as e:
            import logging
            logging.error(f"Erro ao buscar permissões: {str(e)}")
            return {'is_admin': False, 'is_maestro_full': False, 'applications': [], 'portal_tab_access': False, 'portal_apps': []}
    
    def get_all_users(self) -> list:
        """Busca todos os usuários com informações de grupo"""
        try:
            result = self.supabase.table('maestro_users').select(
                'id, username, email, active, created_at, last_login, group_id, maestro_user_groups(id, name, description)'
            ).order('username', desc=False).execute()
            
            users = []
            for user in result.data:
                # Garantir que campos básicos existam
                if not isinstance(user, dict):
                    continue
                
                # Remover password_hash se existir
                user.pop('password_hash', None)
                
                # Processar grupo
                group_data = user.get('maestro_user_groups')
                if group_data:
                    if isinstance(group_data, list) and len(group_data) > 0:
                        user['group'] = group_data[0]
                    elif isinstance(group_data, dict):
                        user['group'] = group_data
                else:
                    user['group'] = None
                
                # Garantir que campos essenciais existam
                user.setdefault('id', None)
                user.setdefault('username', '')
                user.setdefault('email', None)
                user.setdefault('active', True)
                user.setdefault('last_login', None)
                
                users.append(user)
            
            # Ordenação adicional case-insensitive no Python para garantir
            users.sort(key=lambda x: (x.get('username') or '').lower())
            
            return users
        except Exception as e:
            import logging
            logging.error(f"Erro ao buscar usuários: {str(e)}")
            import traceback
            logging.error(traceback.format_exc())
            return []

    def get_users_paginated(self, search_term: str = None, page: int = 1, per_page: int = 20) -> tuple:
        """Retorna (lista de usuários da página, total de usuários) com busca opcional e paginação."""
        users = self.get_all_users()
        if search_term:
            term = (search_term or '').strip().lower()
            if term:
                users = [
                    u for u in users
                    if term in (u.get('username') or '').lower() or term in (u.get('email') or '').lower()
                ]
        total = len(users)
        start = (page - 1) * per_page
        end = start + per_page
        page_users = users[start:end]
        return (page_users, total)
    
    def get_all_groups(self) -> list:
        """Busca todos os grupos"""
        try:
            result = self.supabase.table('maestro_user_groups').select('*').order('name').execute()
            return result.data
        except Exception:
            return []
    
    def get_all_applications(self) -> list:
        """Busca todas as aplicações"""
        try:
            result = self.supabase.table('maestro_applications').select('*').eq('active', True).order('display_name').execute()
            return result.data
        except Exception:
            return []
    
    def update_user_group(self, user_id: int, group_id: int) -> dict:
        """Atualiza grupo do usuário"""
        try:
            result = self.supabase.table('maestro_users').update({'group_id': group_id}).eq('id', user_id).execute()
            if result.data:
                return {'success': True, 'message': 'Grupo atualizado com sucesso'}
            return {'success': False, 'message': 'Erro ao atualizar grupo'}
        except Exception as e:
            return {'success': False, 'message': f'Erro: {str(e)}'}
    
    def grant_application_access(self, user_id: int, application_id: int, granted_by: int = None) -> dict:
        """Concede acesso a uma aplicação para um usuário"""
        try:
            data = {
                'user_id': user_id,
                'application_id': application_id
            }
            if granted_by:
                data['granted_by'] = granted_by
            
            result = self.supabase.table('maestro_user_application_access').insert(data).execute()
            if result.data:
                return {'success': True, 'message': 'Acesso concedido com sucesso'}
            return {'success': False, 'message': 'Erro ao conceder acesso'}
        except Exception as e:
            error_msg = str(e)
            if 'duplicate' in error_msg.lower() or 'unique' in error_msg.lower():
                return {'success': False, 'message': 'Usuário já possui acesso a esta aplicação'}
            return {'success': False, 'message': f'Erro: {str(e)}'}
    
    def revoke_application_access(self, user_id: int, application_id: int) -> dict:
        """Revoga acesso a uma aplicação de um usuário"""
        try:
            result = self.supabase.table('maestro_user_application_access').delete().eq('user_id', user_id).eq('application_id', application_id).execute()
            return {'success': True, 'message': 'Acesso revogado com sucesso'}
        except Exception as e:
            return {'success': False, 'message': f'Erro: {str(e)}'}
    
    def get_user_applications(self, user_id: int) -> list:
        """Busca aplicações permitidas para um usuário"""
        try:
            result = self.supabase.table('maestro_user_application_access').select(
                'application_id, maestro_applications(*)'
            ).eq('user_id', user_id).execute()
            
            applications = []
            for item in result.data:
                if item.get('maestro_applications'):
                    app = item['maestro_applications']
                    if isinstance(app, list) and len(app) > 0:
                        app = app[0]
                    applications.append(app)
            return applications
        except Exception:
            return []

# Instância global do gerenciador de autenticação
auth_manager = AuthManager()

def login_required(f):
    """Decorator para proteger rotas que requerem autenticação"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Permitir requisições OPTIONS (preflight CORS) sem autenticação
        # Safari/MacBooks fazem muitas requisições OPTIONS
        from flask import request
        if request.method == 'OPTIONS':
            from flask import Response
            response = Response()
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, PATCH, OPTIONS, HEAD'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, Accept, Origin'
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Max-Age'] = '3600'
            return response
        
        if 'user_id' not in session:
            flash('Você precisa fazer login para acessar esta página.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator para proteger rotas que requerem permissão de administrador"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id or not auth_manager.is_admin(user_id):
            flash('Acesso negado. Você precisa de permissão de administrador.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def init_auth(app):
    """Inicializa configurações de autenticação no Flask"""
    secret_key = os.getenv('SECRET_KEY', '').strip().replace('\r', '').replace('\n', '')
    
    # Se não houver SECRET_KEY, usar uma chave padrão para desenvolvimento local
    # Em produção, sempre deve estar configurada no .env
    if not secret_key or secret_key == 'change-this-secret-key-in-production':
        import logging
        import secrets
        # Gerar uma chave temporária para desenvolvimento
        secret_key = secrets.token_hex(32)
        logging.warning("SECRET_KEY não configurada no .env! Usando chave temporária para desenvolvimento.")
        logging.warning("⚠️  ATENÇÃO: Configure SECRET_KEY no .env para produção!")
    
    app.secret_key = secret_key
    
    # SESSION_COOKIE_SECURE deve ser True quando usando HTTPS
    # Se configurado como True no .env, assumir que HTTPS está ativo (via Nginx)
    session_secure = os.getenv('SESSION_COOKIE_SECURE', 'True').lower() == 'true'
    # Se True no .env, usar True (HTTPS está ativo via Nginx)
    # Se False no .env, usar False (desenvolvimento local sem HTTPS)
    app.config['SESSION_COOKIE_SECURE'] = session_secure
    app.config['SESSION_COOKIE_HTTPONLY'] = os.getenv('SESSION_COOKIE_HTTPONLY', 'True').lower() == 'true'
    
    # Safari/macOS requer 'None' ou 'Lax' para SameSite
    # 'None' requer Secure=True (HTTPS), então usamos 'Lax' para HTTP
    session_samesite = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
    # Se HTTPS está ativo (session_secure=True), pode usar 'None' ou 'Lax'
    # Se HTTP (session_secure=False), usar 'Lax' para compatibilidade
    if session_samesite == 'None' and not session_secure:
        # Se tentar usar 'None' sem HTTPS, forçar 'Lax' para compatibilidade
        session_samesite = 'Lax'
    # Se HTTPS está ativo e não especificado, usar 'Lax' (compatível com HTTPS)
    if session_secure and session_samesite == 'Lax':
        # 'Lax' funciona bem com HTTPS
        pass
    
    # Configurações adicionais para compatibilidade com Safari/macOS (HTTP sem SSL)
    app.config['SESSION_COOKIE_DOMAIN'] = None  # Não definir domínio específico
    app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 horas
    
    # Configurações específicas para MacBooks/Safari
    # IMPORTANTE: Safari bloqueia cookies SameSite=None sem Secure, então usamos Lax
    # Com HTTPS (Secure=True), 'Lax' funciona perfeitamente
    app.config['SESSION_COOKIE_SAMESITE'] = session_samesite  # Lax funciona com HTTP e HTTPS
    # SESSION_COOKIE_HTTPONLY e SESSION_COOKIE_SECURE já foram configurados acima
    
    # Configurações de sessão para melhor compatibilidade com Safari
    app.config['SESSION_REFRESH_EACH_REQUEST'] = False  # Não renovar sempre (pode causar problemas no Safari)
    app.config['SESSION_USE_SIGNER'] = True  # Assinar cookies para segurança
    
    # Configurações adicionais para Safari
    app.config['SESSION_COOKIE_PATH'] = '/'  # Cookies disponíveis em todo o site
    app.config['SESSION_COOKIE_NAME'] = 'maestro_session'  # Nome específico para evitar conflitos
    
    # Safari precisa que o cookie seja explícito sobre o domínio
    # Não definir SESSION_COOKIE_DOMAIN permite que funcione em qualquer domínio/IP
    
    # Log de configuração (sem expor valores sensíveis)
    import logging
    logging.info(f"Sessão configurada para MacBooks: SECURE={session_secure}, HTTPONLY={app.config['SESSION_COOKIE_HTTPONLY']}, SAMESITE={app.config['SESSION_COOKIE_SAMESITE']}")

