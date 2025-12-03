"""
Módulo de Monitoramento de Performance
Registra métricas básicas de requisições e performance
"""
import time
import logging
from functools import wraps
from flask import request, g
from collections import defaultdict
import threading

# Configurar logging
monitor_logger = logging.getLogger('monitoring')
monitor_logger.setLevel(logging.INFO)

# Métricas globais (thread-safe)
metrics = {
    'requests_total': 0,
    'requests_by_status': defaultdict(int),
    'requests_by_route': defaultdict(int),
    'response_times': [],
    'errors': 0,
    'proxy_requests': 0
}
metrics_lock = threading.Lock()

def record_request_time(f):
    """Decorator para registrar tempo de resposta"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        try:
            response = f(*args, **kwargs)
            response_time = time.time() - start_time
            
            # Registrar métricas
            with metrics_lock:
                metrics['requests_total'] += 1
                status_code = response.status_code if hasattr(response, 'status_code') else 200
                metrics['requests_by_status'][status_code] += 1
                metrics['requests_by_route'][request.path] += 1
                metrics['response_times'].append(response_time)
                
                # Manter apenas últimos 1000 tempos de resposta
                if len(metrics['response_times']) > 1000:
                    metrics['response_times'] = metrics['response_times'][-1000:]
                
                # Registrar erros
                if status_code >= 400:
                    metrics['errors'] += 1
                
                # Registrar requisições de proxy
                if request.path.startswith('/proxy/'):
                    metrics['proxy_requests'] += 1
            
            # Log de requisições lentas (> 2 segundos)
            if response_time > 2.0:
                monitor_logger.warning(
                    f"Requisição lenta: {request.method} {request.path} "
                    f"levou {response_time:.2f}s (Status: {status_code})"
                )
            
            return response
        except Exception as e:
            response_time = time.time() - start_time
            with metrics_lock:
                metrics['errors'] += 1
            monitor_logger.error(
                f"Erro na requisição: {request.method} {request.path} "
                f"após {response_time:.2f}s - {str(e)}"
            )
            raise
    
    return decorated_function

def get_metrics():
    """Retorna métricas atuais"""
    with metrics_lock:
        avg_response_time = (
            sum(metrics['response_times']) / len(metrics['response_times'])
            if metrics['response_times'] else 0
        )
        
        return {
            'requests_total': metrics['requests_total'],
            'requests_by_status': dict(metrics['requests_by_status']),
            'requests_by_route': dict(metrics['requests_by_route']),
            'avg_response_time': round(avg_response_time, 3),
            'errors': metrics['errors'],
            'proxy_requests': metrics['proxy_requests'],
            'error_rate': round(
                (metrics['errors'] / metrics['requests_total'] * 100)
                if metrics['requests_total'] > 0 else 0,
                2
            )
        }

def reset_metrics():
    """Reseta todas as métricas (útil para testes)"""
    with metrics_lock:
        metrics['requests_total'] = 0
        metrics['requests_by_status'].clear()
        metrics['requests_by_route'].clear()
        metrics['response_times'].clear()
        metrics['errors'] = 0
        metrics['proxy_requests'] = 0

def log_performance_summary():
    """Loga resumo de performance (chamar periodicamente)"""
    m = get_metrics()
    monitor_logger.info(
        f"Performance: {m['requests_total']} requisições, "
        f"tempo médio: {m['avg_response_time']}s, "
        f"erros: {m['errors']} ({m['error_rate']}%), "
        f"proxy: {m['proxy_requests']}"
    )

