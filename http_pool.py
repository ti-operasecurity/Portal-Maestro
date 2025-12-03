"""
Módulo de Pool de Conexões HTTP
Otimiza requisições HTTP usando Session com pool de conexões
"""
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging

# Configurar logging
logger = logging.getLogger(__name__)

class HTTPConnectionPool:
    """Gerenciador de pool de conexões HTTP para melhor performance"""
    
    def __init__(self):
        self.sessions = {}
        self._setup_default_session()
    
    def _setup_default_session(self):
        """Configura sessão padrão com pool de conexões otimizado"""
        # Estratégia de retry para requisições falhadas
        retry_strategy = Retry(
            total=3,  # Total de tentativas
            backoff_factor=0.3,  # Tempo de espera entre tentativas
            status_forcelist=[429, 500, 502, 503, 504],  # Status codes para retry
            allowed_methods=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST", "PATCH"]
        )
        
        # Adapter com pool de conexões
        adapter = HTTPAdapter(
            pool_connections=10,  # Número de pools de conexão (por host)
            pool_maxsize=20,  # Máximo de conexões por pool
            max_retries=retry_strategy,
            pool_block=False  # Não bloquear se pool estiver cheio
        )
        
        # Criar sessão padrão
        self.default_session = requests.Session()
        self.default_session.mount("http://", adapter)
        self.default_session.mount("https://", adapter)
        
        # Headers padrão
        self.default_session.headers.update({
            'User-Agent': 'Maestro-Portal/1.0',
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        })
        
        logger.info("Pool de conexões HTTP inicializado: 10 pools, 20 conexões por pool")
    
    def get_session(self, base_url=None):
        """
        Retorna uma sessão HTTP com pool de conexões
        
        Args:
            base_url: URL base para criar sessão específica (opcional)
        
        Returns:
            requests.Session: Sessão configurada com pool
        """
        if base_url:
            # Criar sessão específica para um host se necessário
            if base_url not in self.sessions:
                retry_strategy = Retry(
                    total=3,
                    backoff_factor=0.3,
                    status_forcelist=[429, 500, 502, 503, 504],
                    allowed_methods=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST", "PATCH"]
                )
                
                adapter = HTTPAdapter(
                    pool_connections=5,
                    pool_maxsize=10,
                    max_retries=retry_strategy,
                    pool_block=False
                )
                
                session = requests.Session()
                session.mount("http://", adapter)
                session.mount("https://", adapter)
                session.headers.update({
                    'User-Agent': 'Maestro-Portal/1.0',
                    'Accept': '*/*',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive'
                })
                
                self.sessions[base_url] = session
                logger.debug(f"Sessão criada para {base_url}")
            
            return self.sessions[base_url]
        
        return self.default_session
    
    def close_all(self):
        """Fecha todas as sessões e limpa pools"""
        for session in self.sessions.values():
            session.close()
        self.sessions.clear()
        self.default_session.close()
        logger.info("Todas as sessões HTTP foram fechadas")

# Instância global do pool de conexões
http_pool = HTTPConnectionPool()

