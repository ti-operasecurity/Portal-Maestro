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

